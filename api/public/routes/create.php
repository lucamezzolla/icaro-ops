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

$origin = strtoupper(trim((string)($payload['origin_airport_icao_code'] ?? '')));
$destination = strtoupper(trim((string)($payload['destination_airport_icao_code'] ?? '')));
$departureTime = trim((string)($payload['scheduled_departure_time_utc'] ?? '10:00'));
$ticketPrice = (float)($payload['ticket_price'] ?? 145.00);
$aircraftId = (int)($payload['aircraft_id'] ?? 0);

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

$pdo = db();

try {
    $pdo->beginTransaction();

    $companyStmt = $pdo->prepare("
        SELECT id, currency_code, base_airport_icao_code
        FROM companies
        WHERE id = :company_id
        LIMIT 1
    ");
    $companyStmt->execute(['company_id' => $companyId]);
    $company = $companyStmt->fetch();

    if (!$company) {
        $pdo->rollBack();
        json_response(['error' => 'COMPANY_NOT_FOUND'], 404);
    }

    $originAirport = fetch_airport($pdo, $origin);
    $destinationAirport = fetch_airport($pdo, $destination);

    if (!$originAirport || !$destinationAirport) {
        $pdo->rollBack();
        json_response(['error' => 'AIRPORT_NOT_FOUND'], 404);
    }

    if ($originAirport['latitude'] === null || $originAirport['longitude'] === null || $destinationAirport['latitude'] === null || $destinationAirport['longitude'] === null) {
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

    if ($aircraftId <= 0) {
        $aircraftId = find_preferred_c208_aircraft_id($pdo, $companyId, $origin);
    } else {
        if (!company_owns_aircraft($pdo, $companyId, $aircraftId)) {
            $pdo->rollBack();
            json_response(['error' => 'AIRCRAFT_NOT_OWNED'], 403);
        }
    }

    $pilots = fetch_eligible_pilots($pdo, $companyId);

    if (count($pilots) < 2) {
        $pdo->rollBack();
        json_response([
            'error' => 'MISSING_PILOTS',
            'message' => 'You need two active pilots with CPL and C208_TYPE before planning Cessna passenger routes.',
        ], 409);
    }

    $insert = $pdo->prepare("
        INSERT INTO company_routes (
          company_id,
          aircraft_id,
          origin_airport_icao_code,
          destination_airport_icao_code,
          scheduled_departure_time_utc,
          recurrence_type,
          assigned_pilot_1_id,
          assigned_pilot_2_id,
          assigned_technician_id,
          planned_distance_km,
          planned_duration_minutes,
          ticket_price,
          currency_code,
          status
        ) VALUES (
          :company_id,
          :aircraft_id,
          :origin,
          :destination,
          :departure_time,
          'DAILY',
          :pilot_1,
          :pilot_2,
          NULL,
          :distance_km,
          :duration_minutes,
          :ticket_price,
          :currency_code,
          'ACTIVE'
        )
    ");

    $insert->execute([
        'company_id' => $companyId,
        'aircraft_id' => $aircraftId > 0 ? $aircraftId : null,
        'origin' => $origin,
        'destination' => $destination,
        'departure_time' => $departureTime,
        'pilot_1' => (int)$pilots[0]['id'],
        'pilot_2' => (int)$pilots[1]['id'],
        'distance_km' => number_format($distanceKm, 2, '.', ''),
        'duration_minutes' => $durationMinutes,
        'ticket_price' => $ticketPrice,
        'currency_code' => $company['currency_code'],
    ]);

    $routeId = (int)$pdo->lastInsertId();

    $pdo->commit();

    json_response([
        'route_id' => $routeId,
        'origin_airport_icao_code' => $origin,
        'destination_airport_icao_code' => $destination,
        'scheduled_departure_time_utc' => $departureTime,
        'planned_distance_km' => number_format($distanceKm, 2, '.', ''),
        'planned_duration_minutes' => $durationMinutes,
        'aircraft_id' => $aircraftId > 0 ? $aircraftId : null,
        'pilot_1_name' => $pilots[0]['display_name'],
        'pilot_2_name' => $pilots[1]['display_name'],
        'message' => 'Route created. Technicians are handled by maintenance workflows, not by route planning.',
    ], 201);
} catch (Throwable $exception) {
    if ($pdo->inTransaction()) {
        $pdo->rollBack();
    }

    json_response([
        'error' => 'DATABASE_ERROR',
        'message' => 'Unable to create route.',
    ], 500);
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
        SELECT id, model_code, cruise_speed_kmh, range_km
        FROM aircraft_models
        WHERE model_code = 'C208B_GRAND_CARAVAN_EX'
        LIMIT 1
    ");
    $stmt->execute();
    $row = $stmt->fetch();
    return $row ?: null;
}

function find_preferred_c208_aircraft_id(PDO $pdo, int $companyId, string $origin): int
{
    $stmt = $pdo->prepare("
        SELECT ca.id
        FROM company_aircraft ca
        JOIN aircraft_models am
          ON am.id = ca.aircraft_model_id
        WHERE ca.company_id = :company_id
          AND am.model_code = 'C208B_GRAND_CARAVAN_EX'
        ORDER BY
          CASE WHEN ca.current_airport_icao_code = :origin AND ca.status IN ('AVAILABLE', 'PARKED') THEN 0 ELSE 1 END,
          ca.id
        LIMIT 1
    ");
    $stmt->execute([
        'company_id' => $companyId,
        'origin' => $origin,
    ]);

    return (int)($stmt->fetchColumn() ?: 0);
}

function company_owns_aircraft(PDO $pdo, int $companyId, int $aircraftId): bool
{
    $stmt = $pdo->prepare("
        SELECT id
        FROM company_aircraft
        WHERE id = :aircraft_id
          AND company_id = :company_id
        LIMIT 1
    ");
    $stmt->execute([
        'aircraft_id' => $aircraftId,
        'company_id' => $companyId,
    ]);

    return (bool)$stmt->fetchColumn();
}

function fetch_eligible_pilots(PDO $pdo, int $companyId): array
{
    $stmt = $pdo->prepare("
        SELECT s.id, s.display_name
        FROM company_staff s
        WHERE s.company_id = :company_id
          AND s.staff_role = 'PILOT'
          AND s.employment_status = 'ACTIVE'
          AND EXISTS (
            SELECT 1 FROM company_staff_licenses l
            WHERE l.company_staff_id = s.id
              AND l.license_code = 'CPL'
          )
          AND EXISTS (
            SELECT 1 FROM company_staff_licenses l
            WHERE l.company_staff_id = s.id
              AND l.license_code = 'C208_TYPE'
          )
        ORDER BY s.reliability_score DESC, s.fatigue_score ASC, s.id
        LIMIT 2
    ");
    $stmt->execute(['company_id' => $companyId]);
    return $stmt->fetchAll();
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
