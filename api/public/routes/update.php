<?php
declare(strict_types=1);

require __DIR__ . '/../../lib/bootstrap.php';
require __DIR__ . '/../../lib/session.php';

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    json_response(['error' => 'METHOD_NOT_ALLOWED'], 405);
}

$session = require_auth_session();
$companyId = $session['company_id'];
$payload = read_json_body();

$routeId = (int)($payload['route_id'] ?? 0);
$origin = strtoupper(trim((string)($payload['origin_airport_icao_code'] ?? '')));
$destination = strtoupper(trim((string)($payload['destination_airport_icao_code'] ?? '')));
$departureTime = trim((string)($payload['scheduled_departure_time_utc'] ?? ''));
$ticketPrice = (float)($payload['ticket_price'] ?? -1);
$autoDispatchEnabled = array_key_exists('auto_dispatch_enabled', $payload) ? (bool)$payload['auto_dispatch_enabled'] : true;
$allowBackupAircraft = array_key_exists('allow_backup_aircraft', $payload) ? (bool)$payload['allow_backup_aircraft'] : true;

if ($routeId <= 0) {
    json_response(['error' => 'VALIDATION_ERROR', 'message' => 'route_id is required.'], 422);
}

if (!preg_match('/^[A-Z0-9]{4}$/', $origin) || !preg_match('/^[A-Z0-9]{4}$/', $destination)) {
    json_response(['error' => 'INVALID_AIRPORT_CODE'], 422);
}

if ($origin === $destination) {
    json_response(['error' => 'INVALID_ROUTE', 'message' => 'Origin and destination must be different.'], 422);
}

if (!preg_match('/^\d{2}:\d{2}(:\d{2})?$/', $departureTime)) {
    json_response(['error' => 'INVALID_DEPARTURE_TIME'], 422);
}

if (strlen($departureTime) === 5) {
    $departureTime .= ':00';
}

if ($ticketPrice < 0) {
    json_response(['error' => 'INVALID_TICKET_PRICE'], 422);
}

$pdo = db();

try {
    $pdo->beginTransaction();

    $routeStmt = $pdo->prepare("
        SELECT *
        FROM company_routes
        WHERE id = :route_id
          AND company_id = :company_id
        LIMIT 1
        FOR UPDATE
    ");
    $routeStmt->execute([
        'route_id' => $routeId,
        'company_id' => $companyId,
    ]);
    $route = $routeStmt->fetch();

    if (!$route) {
        $pdo->rollBack();
        json_response(['error' => 'ROUTE_NOT_FOUND'], 404);
    }

    $activeFlightStmt = $pdo->prepare("
        SELECT COUNT(*)
        FROM scheduled_flight_instances
        WHERE route_id = :route_id
          AND status IN ('SCHEDULED', 'IN_FLIGHT')
    ");
    $activeFlightStmt->execute(['route_id' => $routeId]);

    if ((int)$activeFlightStmt->fetchColumn() > 0) {
        $pdo->rollBack();
        json_response([
            'error' => 'ROUTE_HAS_ACTIVE_FLIGHTS',
            'message' => 'This route has active/scheduled flights. Complete or cancel them before editing the route.',
        ], 409);
    }

    $originAirport = fetch_airport($pdo, $origin);
    $destinationAirport = fetch_airport($pdo, $destination);

    if (!$originAirport || !$destinationAirport) {
        $pdo->rollBack();
        json_response(['error' => 'AIRPORT_NOT_FOUND'], 404);
    }

    if (
        $originAirport['latitude'] === null ||
        $originAirport['longitude'] === null ||
        $destinationAirport['latitude'] === null ||
        $destinationAirport['longitude'] === null
    ) {
        $pdo->rollBack();
        json_response(['error' => 'AIRPORT_COORDINATES_MISSING'], 409);
    }

    $model = fetch_c208_model($pdo);
    if (!$model) {
        $pdo->rollBack();
        json_response(['error' => 'AIRCRAFT_MODEL_NOT_FOUND'], 500);
    }

    $distanceKm = haversine_km(
        (float)$originAirport['latitude'],
        (float)$originAirport['longitude'],
        (float)$destinationAirport['latitude'],
        (float)$destinationAirport['longitude']
    );

    if ($distanceKm > (float)$model['range_km']) {
        $pdo->rollBack();
        json_response([
            'error' => 'ROUTE_OUT_OF_RANGE',
            'message' => 'The route distance is outside Cessna 208B range.',
        ], 409);
    }

    $durationMinutes = max(20, (int)ceil(($distanceKm / max(1, (float)$model['cruise_speed_kmh'])) * 60 + 15));

    $update = $pdo->prepare("
        UPDATE company_routes
        SET
          origin_airport_icao_code = :origin,
          destination_airport_icao_code = :destination,
          scheduled_departure_time_utc = :departure_time,
          auto_dispatch_enabled = :auto_dispatch_enabled,
          allow_backup_aircraft = :allow_backup_aircraft,
          planned_distance_km = :distance_km,
          planned_duration_minutes = :duration_minutes,
          ticket_price = :ticket_price,
          status = 'ACTIVE',
          updated_at_utc = CURRENT_TIMESTAMP
        WHERE id = :route_id
          AND company_id = :company_id
    ");

    $update->execute([
        'origin' => $origin,
        'destination' => $destination,
        'departure_time' => $departureTime,
        'auto_dispatch_enabled' => $autoDispatchEnabled ? 1 : 0,
        'allow_backup_aircraft' => $allowBackupAircraft ? 1 : 0,
        'distance_km' => number_format($distanceKm, 2, '.', ''),
        'duration_minutes' => $durationMinutes,
        'ticket_price' => number_format($ticketPrice, 2, '.', ''),
        'route_id' => $routeId,
        'company_id' => $companyId,
    ]);

    $pdo->commit();

    json_response([
        'route_id' => $routeId,
        'origin_airport_icao_code' => $origin,
        'destination_airport_icao_code' => $destination,
        'scheduled_departure_time_utc' => $departureTime,
        'planned_distance_km' => number_format($distanceKm, 2, '.', ''),
        'planned_duration_minutes' => $durationMinutes,
        'ticket_price' => number_format($ticketPrice, 2, '.', ''),
        'auto_dispatch_enabled' => $autoDispatchEnabled,
        'allow_backup_aircraft' => $allowBackupAircraft,
        'status' => 'ACTIVE',
    ]);
} catch (Throwable $exception) {
    if ($pdo->inTransaction()) {
        $pdo->rollBack();
    }

    json_response(['error' => 'DATABASE_ERROR', 'message' => 'Unable to update route.'], 500);
}

function fetch_airport(PDO $pdo, string $icao): ?array
{
    $stmt = $pdo->prepare("SELECT icao_code, name, latitude, longitude FROM airports WHERE icao_code = :icao LIMIT 1");
    $stmt->execute(['icao' => $icao]);
    $row = $stmt->fetch();
    return $row ?: null;
}

function fetch_c208_model(PDO $pdo): ?array
{
    $stmt = $pdo->prepare("
        SELECT cruise_speed_kmh, range_km
        FROM aircraft_models
        WHERE model_code = 'C208B_GRAND_CARAVAN_EX'
        LIMIT 1
    ");
    $stmt->execute();
    $row = $stmt->fetch();
    return $row ?: null;
}

function haversine_km(float $lat1, float $lon1, float $lat2, float $lon2): float
{
    $earthRadiusKm = 6371.0;
    $dLat = deg2rad($lat2 - $lat1);
    $dLon = deg2rad($lon2 - $lon1);
    $a = sin($dLat / 2) ** 2 + cos(deg2rad($lat1)) * cos(deg2rad($lat2)) * sin($dLon / 2) ** 2;
    $c = 2 * atan2(sqrt($a), sqrt(1 - $a));
    return $earthRadiusKm * $c;
}
