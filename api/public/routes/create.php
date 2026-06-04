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

$origin = strtoupper(trim((string)($payload['origin_airport_icao_code'] ?? 'LIRA')));
$destination = strtoupper(trim((string)($payload['destination_airport_icao_code'] ?? 'LIML')));
$departureTime = trim((string)($payload['scheduled_departure_time_utc'] ?? '10:00'));
$ticketPrice = (float)($payload['ticket_price'] ?? 145.00);
$aircraftId = (int)($payload['aircraft_id'] ?? 0);

if (!preg_match('/^[A-Z0-9]{4}$/', $origin) || !preg_match('/^[A-Z0-9]{4}$/', $destination)) {
    json_response(['error' => 'INVALID_AIRPORT_CODE'], 422);
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

    $airportStmt = $pdo->prepare("
        SELECT icao_code, name, latitude, longitude
        FROM airports
        WHERE icao_code IN (:origin, :destination)
    ");
    // MariaDB/PDO named placeholders cannot be reused in all modes; use direct two queries.
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

    if ($aircraftId <= 0) {
        $aircraftStmt = $pdo->prepare("
            SELECT ca.id
            FROM company_aircraft ca
            JOIN aircraft_models am
              ON am.id = ca.aircraft_model_id
            WHERE ca.company_id = :company_id
              AND ca.status IN ('AVAILABLE', 'PARKED')
              AND ca.home_base_icao_code = :origin
              AND am.model_code = 'C208B_GRAND_CARAVAN_EX'
            ORDER BY ca.id
            LIMIT 1
        ");
        $aircraftStmt->execute([
            'company_id' => $companyId,
            'origin' => $origin,
        ]);
        $aircraftId = (int)($aircraftStmt->fetchColumn() ?: 0);
    }

    $aircraft = fetch_aircraft($pdo, $companyId, $aircraftId);

    if (!$aircraft) {
        $pdo->rollBack();
        json_response(['error' => 'NO_AVAILABLE_AIRCRAFT', 'message' => 'No available Cessna 208B at the origin airport.'], 409);
    }

    $distanceKm = haversine_km(
        (float)$originAirport['latitude'],
        (float)$originAirport['longitude'],
        (float)$destinationAirport['latitude'],
        (float)$destinationAirport['longitude']
    );

    if ($distanceKm > (float)$aircraft['range_km']) {
        $pdo->rollBack();
        json_response(['error' => 'ROUTE_OUT_OF_RANGE'], 409);
    }

    $durationMinutes = max(20, (int)ceil(($distanceKm / max(1, (float)$aircraft['cruise_speed_kmh'])) * 60 + 15));

    $pilots = fetch_eligible_pilots($pdo, $companyId);
    $technician = fetch_eligible_technician($pdo, $companyId);

    if (count($pilots) < 2) {
        $pdo->rollBack();
        json_response(['error' => 'MISSING_PILOTS', 'message' => 'Two active pilots with CPL and C208_TYPE are required.'], 409);
    }

    if (!$technician) {
        $pdo->rollBack();
        json_response(['error' => 'MISSING_TECHNICIAN', 'message' => 'One active technician with C208_MAINT is required.'], 409);
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
          :technician,
          :distance_km,
          :duration_minutes,
          :ticket_price,
          :currency_code,
          'ACTIVE'
        )
    ");

    $insert->execute([
        'company_id' => $companyId,
        'aircraft_id' => $aircraftId,
        'origin' => $origin,
        'destination' => $destination,
        'departure_time' => $departureTime,
        'pilot_1' => (int)$pilots[0]['id'],
        'pilot_2' => (int)$pilots[1]['id'],
        'technician' => (int)$technician['id'],
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
        'aircraft_registration_code' => $aircraft['registration_code'],
        'pilot_1_name' => $pilots[0]['display_name'],
        'pilot_2_name' => $pilots[1]['display_name'],
        'technician_name' => $technician['display_name'],
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

function fetch_aircraft(PDO $pdo, int $companyId, int $aircraftId): ?array
{
    $stmt = $pdo->prepare("
        SELECT
          ca.id,
          ca.registration_code,
          ca.status,
          ca.home_base_icao_code,
          am.model_code,
          am.passenger_capacity_standard,
          am.cruise_speed_kmh,
          am.range_km,
          am.fuel_burn_kg_per_hour,
          am.maintenance_cost_per_hour
        FROM company_aircraft ca
        JOIN aircraft_models am
          ON am.id = ca.aircraft_model_id
        WHERE ca.id = :aircraft_id
          AND ca.company_id = :company_id
          AND ca.status IN ('AVAILABLE', 'PARKED')
        LIMIT 1
    ");
    $stmt->execute([
        'aircraft_id' => $aircraftId,
        'company_id' => $companyId,
    ]);
    $row = $stmt->fetch();
    return $row ?: null;
}

function fetch_eligible_pilots(PDO $pdo, int $companyId): array
{
    $stmt = $pdo->prepare("
        SELECT s.id, s.display_name, s.salary_per_flight, s.revenue_share_percent
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

function fetch_eligible_technician(PDO $pdo, int $companyId): ?array
{
    $stmt = $pdo->prepare("
        SELECT s.id, s.display_name, s.daily_retainer
        FROM company_staff s
        WHERE s.company_id = :company_id
          AND s.staff_role = 'TECHNICIAN'
          AND s.employment_status = 'ACTIVE'
          AND EXISTS (
            SELECT 1 FROM company_staff_licenses l
            WHERE l.company_staff_id = s.id
              AND l.license_code = 'C208_MAINT'
          )
        ORDER BY s.reliability_score DESC, s.fatigue_score ASC, s.id
        LIMIT 1
    ");
    $stmt->execute(['company_id' => $companyId]);
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
