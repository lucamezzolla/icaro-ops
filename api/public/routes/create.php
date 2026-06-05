<?php
declare(strict_types=1);

require __DIR__ . '/../../lib/bootstrap.php';
require __DIR__ . '/../../lib/session.php';

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    json_response(['error' => 'METHOD_NOT_ALLOWED'], 405);
}

$session = require_auth_session();
$companyId = (int)$session['company_id'];
$payload = read_json_body();

$origin = strtoupper(trim((string)($payload['origin_airport_icao_code'] ?? '')));
$destination = strtoupper(trim((string)($payload['destination_airport_icao_code'] ?? '')));
$departure = trim((string)($payload['scheduled_departure_time_utc'] ?? ''));
$ticketPrice = (float)($payload['ticket_price'] ?? $payload['base_ticket_price'] ?? 0);

if (!preg_match('/^[A-Z0-9]{4}$/', $origin) || !preg_match('/^[A-Z0-9]{4}$/', $destination)) {
    json_response(['error' => 'INVALID_AIRPORT_CODE'], 422);
}

if ($origin === $destination) {
    json_response(['error' => 'INVALID_ROUTE'], 422);
}

if (!preg_match('/^\d{2}:\d{2}(:\d{2})?$/', $departure)) {
    json_response(['error' => 'INVALID_DEPARTURE_TIME'], 422);
}

if (strlen($departure) === 5) {
    $departure .= ':00';
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

$companyStmt = $pdo->prepare("
    SELECT currency_code
    FROM companies
    WHERE id = :company_id
    LIMIT 1
");
$companyStmt->execute(['company_id' => $companyId]);
$company = $companyStmt->fetch() ?: ['currency_code' => 'EUR'];

$modelStmt = $pdo->prepare("
    SELECT id, cruise_speed_kmh
    FROM aircraft_models
    WHERE model_code = 'C208B_GRAND_CARAVAN_EX'
    LIMIT 1
");
$modelStmt->execute();
$preferredModel = $modelStmt->fetch();

$distanceKm = haversine_km(
    (float)$originAirport['latitude'],
    (float)$originAirport['longitude'],
    (float)$destinationAirport['latitude'],
    (float)$destinationAirport['longitude']
);

$cruiseSpeed = max(1.0, (float)($preferredModel['cruise_speed_kmh'] ?? 340));
$durationMinutes = max(20, (int)ceil(($distanceKm / $cruiseSpeed) * 60 + 15));

$routeScope = ((string)($originAirport['country_id'] ?? '') === (string)($destinationAirport['country_id'] ?? ''))
    ? 'DOMESTIC'
    : 'INTERNATIONAL';

$routeScopeCode = $routeScope === 'DOMESTIC' ? 'DOM' : 'INT';
$routeCode = "AR-{$origin}-{$destination}-{$routeScopeCode}-PAX";

try {
    $pdo->beginTransaction();

    $routeStmt = $pdo->prepare("
        SELECT id
        FROM air_routes
        WHERE origin_airport_icao_code = :origin
          AND destination_airport_icao_code = :destination
          AND route_scope = :route_scope
          AND route_market = 'PAX'
          AND route_operation_domain = 'CIVIL'
          AND required_aircraft_class = 'LIGHT_COMMERCIAL'
        LIMIT 1
        FOR UPDATE
    ");
    $routeStmt->execute([
        'origin' => $origin,
        'destination' => $destination,
        'route_scope' => $routeScope,
    ]);
    $airRouteId = $routeStmt->fetchColumn();

    if (!$airRouteId) {
        $insertRoute = $pdo->prepare("
            INSERT INTO air_routes (
              route_code,
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
              :origin,
              :destination,
              :route_scope,
              'PAX',
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
            'route_code' => $routeCode,
            'origin' => $origin,
            'destination' => $destination,
            'route_scope' => $routeScope,
            'min_range_km' => number_format($distanceKm, 2, '.', ''),
            'planned_distance_km' => number_format($distanceKm, 2, '.', ''),
            'estimated_block_minutes' => $durationMinutes,
        ]);

        $airRouteId = (int)$pdo->lastInsertId();
    }

    $serviceCode = sprintf(
        'SV-C%03d-%s-%s-%s',
        $companyId,
        $origin,
        $destination,
        str_replace(':', '', substr($departure, 0, 5))
    );

    $existingService = $pdo->prepare("
        SELECT id
        FROM scheduled_services
        WHERE company_id = :company_id
          AND air_route_id = :air_route_id
          AND scheduled_departure_time_utc = :departure
          AND service_status <> 'CANCELLED'
        LIMIT 1
    ");
    $existingService->execute([
        'company_id' => $companyId,
        'air_route_id' => $airRouteId,
        'departure' => $departure,
    ]);

    if ($existingService->fetchColumn()) {
        $pdo->rollBack();
        json_response(['error' => 'SERVICE_ALREADY_EXISTS'], 409);
    }

    $insertService = $pdo->prepare("
        INSERT INTO scheduled_services (
          company_id,
          air_route_id,
          service_code,
          recurrence_type,
          scheduled_departure_time_utc,
          service_status,
          preferred_aircraft_model_id,
          required_aircraft_class,
          base_ticket_price,
          currency_code,
          auto_dispatch_enabled,
          allow_backup_aircraft,
          allow_extra_flights
        ) VALUES (
          :company_id,
          :air_route_id,
          :service_code,
          'DAILY',
          :departure,
          'ACTIVE',
          :preferred_aircraft_model_id,
          'LIGHT_COMMERCIAL',
          :base_ticket_price,
          :currency_code,
          1,
          1,
          1
        )
    ");
    $insertService->execute([
        'company_id' => $companyId,
        'air_route_id' => $airRouteId,
        'service_code' => $serviceCode,
        'departure' => $departure,
        'preferred_aircraft_model_id' => $preferredModel['id'] ?? null,
        'base_ticket_price' => number_format($ticketPrice, 2, '.', ''),
        'currency_code' => $company['currency_code'] ?? 'EUR',
    ]);

    $serviceId = (int)$pdo->lastInsertId();

    $pdo->commit();

    json_response([
        'status' => 'SERVICE_CREATED',
        'message' => 'Scheduled service created over an abstract air route.',
        'air_route_id' => (int)$airRouteId,
        'service_id' => $serviceId,
        'route_code' => $routeCode,
        'service_code' => $serviceCode,
    ]);
} catch (Throwable $exception) {
    if ($pdo->inTransaction()) {
        $pdo->rollBack();
    }

    json_response([
        'error' => 'SERVICE_CREATE_FAILED',
        'message' => 'Unable to create scheduled service.',
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
