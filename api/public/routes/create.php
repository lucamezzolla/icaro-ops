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

$origin = strtoupper(trim((string)($payload['origin_airport_icao_code'] ?? '')));
$destination = strtoupper(trim((string)($payload['destination_airport_icao_code'] ?? '')));
$flightType = strtoupper(trim((string)($payload['service_type'] ?? $payload['flight_type'] ?? 'ON_DEMAND')));
$flightCategory = strtoupper(trim((string)($payload['route_category_code'] ?? $payload['flight_category_code'] ?? '')));
$departure = trim((string)($payload['scheduled_departure_time_utc'] ?? ''));
$ticketPrice = (float)($payload['ticket_price'] ?? $payload['base_ticket_price'] ?? 0);

if (!in_array($flightType, ['SCHEDULED', 'ON_DEMAND'], true)) {
    json_response(['error' => 'INVALID_FLIGHT_TYPE'], 422);
}

if (!preg_match('/^[A-Z0-9]{4}$/', $origin) || !preg_match('/^[A-Z0-9]{4}$/', $destination)) {
    json_response(['error' => 'INVALID_AIRPORT_CODE'], 422);
}

if ($origin === $destination) {
    json_response(['error' => 'INVALID_FLIGHT'], 422);
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

$compatibleModels = compatible_aircraft_models_for_route($pdo, $flightCategory, $distanceKm, 1, 19);

if (!$compatibleModels) {
    json_response([
        'error' => 'NO_COMPATIBLE_MODELS_FOR_FLIGHT',
        'message' => 'No aircraft model is compatible with this flight.',
    ], 409);
}

$preferredModel = $compatibleModels[0];
$compatibleModelCodes = compatible_model_codes_csv($compatibleModels);
$cruiseSpeed = max(1.0, (float)($preferredModel['cruise_speed_kmh'] ?? 340));
$durationMinutes = max(20, (int)ceil(($distanceKm / $cruiseSpeed) * 60 + 15));

/*
 * Legacy hidden air route code: still needed internally for origin/destination.
 * User-visible flight code is generated below as DOM-0001 / INT-0001 / etc.
 */
$hiddenAirRouteCode = "AR-{$origin}-{$destination}-{$flightCategory}-{$routeMarket}";

try {
    $pdo->beginTransaction();

    /*
     * Reuse hidden air_route for the same origin/destination/category.
     * This is not user-visible anymore.
     */
    $routeStmt = $pdo->prepare("
        SELECT id
        FROM air_routes
        WHERE origin_airport_icao_code = :origin
          AND destination_airport_icao_code = :destination
          AND route_scope = :route_scope
          AND route_market = :route_market
          AND route_operation_domain = 'CIVIL'
          AND required_aircraft_class = 'LIGHT_COMMERCIAL'
        LIMIT 1
        FOR UPDATE
    ");
    $routeStmt->execute([
        'origin' => $origin,
        'destination' => $destination,
        'route_scope' => $routeScope,
        'route_market' => $routeMarket,
    ]);

    $airRouteId = $routeStmt->fetchColumn();

    if (!$airRouteId) {
        $routePublicFallback = next_route_public_code($pdo, $flightCategory);

        $insertRoute = $pdo->prepare("
            INSERT INTO air_routes (
              route_code,
              route_category_code,
              route_public_code,
              origin_airport_icao_code,
              destination_airport_icao_code,
              route_scope,
              route_market,
              route_operation_domain,
              required_aircraft_class,
              min_passenger_capacity,
              max_passenger_capacity,
              min_range_km,
              planned_distance_km,
              estimated_block_minutes,
              status
            ) VALUES (
              :route_code,
              :route_category_code,
              :route_public_code,
              :origin,
              :destination,
              :route_scope,
              :route_market,
              'CIVIL',
              'LIGHT_COMMERCIAL',
              1,
              19,
              :min_range_km,
              :planned_distance_km,
              :estimated_block_minutes,
              'ACTIVE'
            )
        ");
        $insertRoute->execute([
            'route_code' => $hiddenAirRouteCode,
            'route_category_code' => $flightCategory,
            'route_public_code' => $routePublicFallback,
            'origin' => $origin,
            'destination' => $destination,
            'route_scope' => $routeScope,
            'route_market' => $routeMarket,
            'min_range_km' => number_format($distanceKm, 2, '.', ''),
            'planned_distance_km' => number_format($distanceKm, 2, '.', ''),
            'estimated_block_minutes' => $durationMinutes,
        ]);

        $airRouteId = (int)$pdo->lastInsertId();
    } else {
        $airRouteId = (int)$airRouteId;
    }

    /*
     * User-visible code for the created flight definition.
     * Cancelled/removed flights never free their number.
     */
    $flightPublicCode = next_flight_public_code($pdo, $flightCategory);

    /*
     * Internal unique code. Includes epoch so recreating the same removed flight
     * can never collide with uq_scheduled_services_code.
     */
    $timePart = $flightType === 'SCHEDULED'
        ? str_replace(':', '', substr((string)$departure, 0, 5))
        : 'ONDEMAND';

    $internalUniqueCode = sprintf(
        '%s-C%03d-%s-%s-%d',
        $flightPublicCode,
        $companyId,
        $flightType === 'SCHEDULED' ? 'SCH' : 'OND',
        $timePart,
        time()
    );

    $columns = table_columns($pdo, 'scheduled_services');

    $values = [];
    put($values, $columns, 'company_id', $companyId);
    put($values, $columns, 'air_route_id', $airRouteId);
    put($values, $columns, 'service_code', $internalUniqueCode);
    put($values, $columns, 'flight_route_code', $flightPublicCode);
    put($values, $columns, 'service_type', $flightType);
    put($values, $columns, 'recurrence_type', $flightType === 'SCHEDULED' ? 'DAILY' : 'ON_DEMAND');
    put($values, $columns, 'scheduled_departure_time_utc', $departure);
    put($values, $columns, 'service_status', 'ACTIVE');
    put($values, $columns, 'preferred_aircraft_model_id', (int)$preferredModel['id']);
    put($values, $columns, 'compatible_aircraft_model_codes', $compatibleModelCodes);
    put($values, $columns, 'required_aircraft_class', 'LIGHT_COMMERCIAL');
    put($values, $columns, 'base_ticket_price', number_format($ticketPrice, 2, '.', ''));
    put($values, $columns, 'currency_code', $company['currency_code'] ?? 'EUR');
    put($values, $columns, 'auto_dispatch_enabled', 1);
    put($values, $columns, 'allow_backup_aircraft', 1);
    put($values, $columns, 'allow_extra_flights', 1);

    $serviceId = insert_dynamic($pdo, 'scheduled_services', $values);

    $pdo->commit();

    json_response([
        'status' => 'FLIGHT_CREATED',
        'flight_code' => $flightPublicCode,
        'internal_service_code' => $internalUniqueCode,
        'flight_type' => $flightType,
        'flight_category_code' => $flightCategory,
        'scheduled_departure_time_utc' => $departure,
        'air_route_id' => $airRouteId,
        'service_id' => $serviceId,
        'compatible_aircraft_model_codes' => $compatibleModelCodes,
        'compatible_aircraft_icao_codes' => compatible_icao_codes_csv($compatibleModels),
    ]);
} catch (Throwable $exception) {
    if ($pdo->inTransaction()) {
        $pdo->rollBack();
    }

    json_response([
        'error' => 'FLIGHT_CREATE_FAILED',
        'message' => $exception->getMessage(),
    ], 500);
}

function fetch_airport(PDO $pdo, string $icao): ?array
{
    $stmt = $pdo->prepare("
        SELECT icao_code, name, country_id, latitude, longitude
        FROM airports
        WHERE icao_code = :icao
        LIMIT 1
    ");
    $stmt->execute(['icao' => $icao]);
    $row = $stmt->fetch();

    return $row ?: null;
}

function table_columns(PDO $pdo, string $tableName): array
{
    $stmt = $pdo->prepare("
        SELECT COLUMN_NAME
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = :table_name
    ");
    $stmt->execute(['table_name' => $tableName]);

    return array_flip(array_map(static fn ($row) => $row['COLUMN_NAME'], $stmt->fetchAll()));
}

function put(array &$values, array $columns, string $column, mixed $value): void
{
    if (isset($columns[$column])) {
        $values[$column] = $value;
    }
}

function insert_dynamic(PDO $pdo, string $tableName, array $values): int
{
    $columns = array_keys($values);
    $quoted = array_map(static fn ($column) => "`{$column}`", $columns);
    $placeholders = array_map(static fn ($column) => ":{$column}", $columns);

    $sql = "INSERT INTO {$tableName} (" . implode(', ', $quoted) . ") VALUES (" . implode(', ', $placeholders) . ")";
    $stmt = $pdo->prepare($sql);

    foreach ($values as $column => $value) {
        $stmt->bindValue(":{$column}", $value);
    }

    $stmt->execute();

    return (int)$pdo->lastInsertId();
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
