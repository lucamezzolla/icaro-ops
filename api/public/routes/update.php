<?php
declare(strict_types=1);

require __DIR__ . '/../../lib/bootstrap.php';
require __DIR__ . '/../../lib/session.php';
require_once __DIR__ . '/../../lib/flight-route-compatibility.php';

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    json_response(['error' => 'METHOD_NOT_ALLOWED'], 405);
}

$session = require_auth_session();
$companyId = (int)$session['company_id'];
$payload = read_json_body();

$serviceId = (int)($payload['service_id'] ?? $payload['route_id'] ?? 0);
$origin = strtoupper(trim((string)($payload['origin_airport_icao_code'] ?? '')));
$destination = strtoupper(trim((string)($payload['destination_airport_icao_code'] ?? '')));
$flightType = strtoupper(trim((string)($payload['service_type'] ?? $payload['flight_type'] ?? 'ON_DEMAND')));
$flightCategory = strtoupper(trim((string)($payload['route_category_code'] ?? $payload['flight_category_code'] ?? '')));
$departure = trim((string)($payload['scheduled_departure_time_utc'] ?? ''));
$ticketPrice = (float)($payload['ticket_price'] ?? $payload['base_ticket_price'] ?? 0);
$selectedModelCodes = normalize_selected_model_codes($payload['selected_aircraft_model_codes'] ?? $payload['aircraft_model_codes'] ?? []);

if ($serviceId <= 0) {
    json_response(['error' => 'INVALID_SERVICE_ID', 'message' => 'service_id is required.'], 422);
}

if (!in_array($flightType, ['SCHEDULED', 'ON_DEMAND'], true)) {
    json_response(['error' => 'INVALID_FLIGHT_TYPE'], 422);
}

if (!preg_match('/^[A-Z0-9]{4}$/', $origin) || !preg_match('/^[A-Z0-9]{4}$/', $destination)) {
    json_response(['error' => 'INVALID_AIRPORT_CODE'], 422);
}

if ($origin === $destination) {
    json_response(['error' => 'INVALID_FLIGHT', 'message' => 'Origin and destination must be different.'], 422);
}

if (!$selectedModelCodes) {
    json_response([
        'error' => 'NO_AIRCRAFT_MODELS_SELECTED',
        'message' => 'Select at least one owned airplane model for this flight.',
    ], 422);
}

if ($flightType === 'SCHEDULED') {
    if (!preg_match('/^\d{2}:\d{2}(:\d{2})?$/', $departure)) {
        json_response(['error' => 'INVALID_DEPARTURE_TIME'], 422);
    }

    if (strlen($departure) === 5) {
        $departure .= ':00';
    }
} else {
    $departure = null;
}

if ($ticketPrice < 0) {
    json_response(['error' => 'INVALID_TICKET_PRICE'], 422);
}

$pdo = db();

$originAirport = fetch_airport($pdo, $origin);
$destinationAirport = fetch_airport($pdo, $destination);

if (!$originAirport || !$destinationAirport) {
    json_response(['error' => 'AIRPORT_NOT_FOUND'], 404);
}

if (
    $originAirport['latitude'] === null ||
    $originAirport['longitude'] === null ||
    $destinationAirport['latitude'] === null ||
    $destinationAirport['longitude'] === null
) {
    json_response(['error' => 'AIRPORT_COORDINATES_MISSING'], 409);
}

$ownedModels = fetch_owned_models_by_code($pdo, $companyId, $selectedModelCodes);

if (count($ownedModels) !== count($selectedModelCodes)) {
    json_response([
        'error' => 'AIRCRAFT_MODEL_NOT_OWNED',
        'message' => 'One or more selected airplane models are not owned by your company.',
    ], 422);
}

$companyStmt = $pdo->prepare("SELECT currency_code FROM companies WHERE id = :company_id LIMIT 1");
$companyStmt->execute(['company_id' => $companyId]);
$company = $companyStmt->fetch() ?: ['currency_code' => 'EUR'];

$distanceKm = haversine_km(
    (float)$originAirport['latitude'],
    (float)$originAirport['longitude'],
    (float)$destinationAirport['latitude'],
    (float)$destinationAirport['longitude']
);

if ($flightCategory === '') {
    $flightCategory = determine_route_category_code($pdo, $origin, $destination, $flightType);
}

$routeScope = route_scope_from_category($flightCategory);
$routeMarket = route_market_from_category($flightCategory);

$preferredModel = $ownedModels[0];
$compatibleModelCodes = implode(',', $selectedModelCodes);
$cruiseSpeed = max(1.0, (float)($preferredModel['cruise_speed_kmh'] ?? 340));
$durationMinutes = max(20, (int)ceil(($distanceKm / $cruiseSpeed) * 60 + 15));
$hiddenAirRouteCode = "AR-{$origin}-{$destination}-{$flightCategory}-{$routeMarket}";

try {
    $pdo->beginTransaction();

    $serviceStmt = $pdo->prepare("\n        SELECT *\n        FROM scheduled_services\n        WHERE id = :service_id\n          AND company_id = :company_id\n          AND service_status <> 'CANCELLED'\n        LIMIT 1\n        FOR UPDATE\n    ");
    $serviceStmt->execute([
        'service_id' => $serviceId,
        'company_id' => $companyId,
    ]);
    $service = $serviceStmt->fetch();

    if (!$service) {
        $pdo->rollBack();
        json_response(['error' => 'SERVICE_NOT_FOUND'], 404);
    }

    $activeFlights = $pdo->prepare("\n        SELECT COUNT(*)\n        FROM scheduled_flight_instances\n        WHERE company_id = :company_id\n          AND scheduled_service_id = :service_id\n          AND status IN ('SCHEDULED', 'BOARDING', 'IN_FLIGHT', 'DELAYED')\n    ");
    $activeFlights->execute([
        'company_id' => $companyId,
        'service_id' => $serviceId,
    ]);

    if ((int)$activeFlights->fetchColumn() > 0) {
        $pdo->rollBack();
        json_response([
            'error' => 'SERVICE_HAS_ACTIVE_FLIGHTS',
            'message' => 'This flight has active or pending flight instances and cannot be edited now.',
        ], 409);
    }

    $routeStmt = $pdo->prepare("\n        SELECT id\n        FROM air_routes\n        WHERE origin_airport_icao_code = :origin\n          AND destination_airport_icao_code = :destination\n          AND route_scope = :route_scope\n          AND route_market = :route_market\n          AND route_operation_domain = 'CIVIL'\n          AND required_aircraft_class = 'LIGHT_COMMERCIAL'\n        LIMIT 1\n        FOR UPDATE\n    ");
    $routeStmt->execute([
        'origin' => $origin,
        'destination' => $destination,
        'route_scope' => $routeScope,
        'route_market' => $routeMarket,
    ]);

    $airRouteId = $routeStmt->fetchColumn();

    if (!$airRouteId) {
        $routePublicFallback = next_route_public_code($pdo, $flightCategory);

        $insertRoute = $pdo->prepare("\n            INSERT INTO air_routes (\n              route_code,\n              route_category_code,\n              route_public_code,\n              origin_airport_icao_code,\n              destination_airport_icao_code,\n              route_scope,\n              route_market,\n              route_operation_domain,\n              required_aircraft_class,\n              min_passenger_capacity,\n              max_passenger_capacity,\n              min_range_km,\n              planned_distance_km,\n              estimated_block_minutes,\n              status\n            ) VALUES (\n              :route_code,\n              :route_category_code,\n              :route_public_code,\n              :origin,\n              :destination,\n              :route_scope,\n              :route_market,\n              'CIVIL',\n              'LIGHT_COMMERCIAL',\n              1,\n              999,\n              0,\n              :planned_distance_km,\n              :estimated_block_minutes,\n              'ACTIVE'\n            )\n        ");
        $insertRoute->execute([
            'route_code' => $hiddenAirRouteCode,
            'route_category_code' => $flightCategory,
            'route_public_code' => $routePublicFallback,
            'origin' => $origin,
            'destination' => $destination,
            'route_scope' => $routeScope,
            'route_market' => $routeMarket,
            'planned_distance_km' => number_format($distanceKm, 2, '.', ''),
            'estimated_block_minutes' => $durationMinutes,
        ]);

        $airRouteId = (int)$pdo->lastInsertId();
    } else {
        $airRouteId = (int)$airRouteId;
    }

    $columns = table_columns($pdo, 'scheduled_services');
    $values = [];

    put($values, $columns, 'air_route_id', $airRouteId);
    put($values, $columns, 'service_type', $flightType);
    put($values, $columns, 'recurrence_type', $flightType === 'SCHEDULED' ? 'DAILY' : 'ON_DEMAND');
    put($values, $columns, 'scheduled_departure_time_utc', $departure);
    put($values, $columns, 'service_status', 'ACTIVE');
    put($values, $columns, 'preferred_aircraft_model_id', (int)$preferredModel['id']);
    put($values, $columns, 'compatible_aircraft_model_codes', $compatibleModelCodes);
    put($values, $columns, 'required_aircraft_class', 'MANUAL_SELECTION');
    put($values, $columns, 'base_ticket_price', number_format($ticketPrice, 2, '.', ''));
    put($values, $columns, 'currency_code', $company['currency_code'] ?? 'EUR');
    put($values, $columns, 'auto_dispatch_enabled', 1);
    put($values, $columns, 'allow_backup_aircraft', 1);
    put($values, $columns, 'allow_extra_flights', 1);

    update_dynamic($pdo, 'scheduled_services', $values, $serviceId, $companyId);

    $pdo->commit();

    json_response([
        'status' => 'FLIGHT_UPDATED',
        'service_id' => $serviceId,
        'flight_code' => $service['flight_route_code'] ?? null,
        'flight_type' => $flightType,
        'flight_category_code' => $flightCategory,
        'scheduled_departure_time_utc' => $departure,
        'air_route_id' => $airRouteId,
        'selected_aircraft_model_codes' => $selectedModelCodes,
        'compatible_aircraft_model_codes' => $compatibleModelCodes,
        'compatible_aircraft_icao_codes' => compatible_icao_codes_csv($ownedModels),
        'message' => 'Flight updated.',
    ]);
} catch (Throwable $exception) {
    if ($pdo->inTransaction()) {
        $pdo->rollBack();
    }

    json_response([
        'error' => 'FLIGHT_UPDATE_FAILED',
        'message' => $exception->getMessage(),
    ], 500);
}

function normalize_selected_model_codes(mixed $value): array
{
    if (is_string($value)) {
        $value = explode(',', $value);
    }

    if (!is_array($value)) {
        return [];
    }

    $codes = [];

    foreach ($value as $code) {
        $code = strtoupper(trim((string)$code));

        if ($code !== '' && preg_match('/^[A-Z0-9_]+$/', $code)) {
            $codes[] = $code;
        }
    }

    return array_values(array_unique($codes));
}

function fetch_owned_models_by_code(PDO $pdo, int $companyId, array $modelCodes): array
{
    if (!$modelCodes) {
        return [];
    }

    $placeholders = implode(',', array_fill(0, count($modelCodes), '?'));

    $stmt = $pdo->prepare("\n        SELECT\n          am.id,\n          am.model_code,\n          am.icao_type_code,\n          am.manufacturer,\n          am.model_name,\n          am.passenger_capacity_standard,\n          am.range_km,\n          am.cruise_speed_kmh\n        FROM aircraft_models am\n        WHERE am.model_code IN ({$placeholders})\n          AND EXISTS (\n            SELECT 1\n            FROM company_aircraft ca\n            WHERE ca.company_id = ?\n              AND ca.aircraft_model_id = am.id\n          )\n        ORDER BY FIELD(am.model_code, {$placeholders})\n    ");

    $params = array_merge($modelCodes, [$companyId], $modelCodes);
    $stmt->execute($params);

    return $stmt->fetchAll();
}

function fetch_airport(PDO $pdo, string $icao): ?array
{
    $stmt = $pdo->prepare("\n        SELECT icao_code, name, country_id, latitude, longitude\n        FROM airports\n        WHERE icao_code = :icao\n        LIMIT 1\n    ");
    $stmt->execute(['icao' => $icao]);
    $row = $stmt->fetch();

    return $row ?: null;
}

function table_columns(PDO $pdo, string $tableName): array
{
    $stmt = $pdo->prepare("\n        SELECT COLUMN_NAME\n        FROM information_schema.COLUMNS\n        WHERE TABLE_SCHEMA = DATABASE()\n          AND TABLE_NAME = :table_name\n    ");
    $stmt->execute(['table_name' => $tableName]);

    return array_flip(array_map(static fn ($row) => $row['COLUMN_NAME'], $stmt->fetchAll()));
}

function put(array &$values, array $columns, string $column, mixed $value): void
{
    if (isset($columns[$column])) {
        $values[$column] = $value;
    }
}

function update_dynamic(PDO $pdo, string $tableName, array $values, int $serviceId, int $companyId): void
{
    if (!$values) {
        return;
    }

    $assignments = array_map(static fn ($column) => "`{$column}` = :{$column}", array_keys($values));
    $sql = "UPDATE {$tableName} SET " . implode(', ', $assignments) . " WHERE id = :service_id AND company_id = :company_id";
    $stmt = $pdo->prepare($sql);

    foreach ($values as $column => $value) {
        $stmt->bindValue(":{$column}", $value);
    }

    $stmt->bindValue(':service_id', $serviceId, PDO::PARAM_INT);
    $stmt->bindValue(':company_id', $companyId, PDO::PARAM_INT);
    $stmt->execute();
}

function haversine_km(float $lat1, float $lon1, float $lat2, float $lon2): float
{
    $earthRadiusKm = 6371.0;
    $dLat = deg2rad($lat2 - $lat1);
    $dLon = deg2rad($lon2 - $lon1);

    $a = sin($dLat / 2) ** 2
        + cos(deg2rad($lat1))
        * cos(deg2rad($lat2))
        * sin($dLon / 2) ** 2;

    $c = 2 * atan2(sqrt($a), sqrt(1 - $a));

    return $earthRadiusKm * $c;
}
