<?php
declare(strict_types=1);

require __DIR__ . '/../../lib/bootstrap.php';
require __DIR__ . '/../../lib/session.php';

$session = require_auth_session();
$companyId = (int)$session['company_id'];

$flightInstanceId = filter_input(INPUT_GET, 'flight_instance_id', FILTER_VALIDATE_INT);
$aircraftId = filter_input(INPUT_GET, 'aircraft_id', FILTER_VALIDATE_INT);

if (!$flightInstanceId && !$aircraftId) {
    json_response([
        'error' => 'INVALID_REQUEST',
        'message' => 'flight_instance_id or aircraft_id is required.',
    ], 422);
}

$pdo = db();

$where = $flightInstanceId
    ? "sfi.id = :flight_instance_id"
    : "sfi.aircraft_id = :aircraft_id AND sfi.status = 'IN_FLIGHT'";

$params = ['company_id' => $companyId];

if ($flightInstanceId) {
    $params['flight_instance_id'] = $flightInstanceId;
} else {
    $params['aircraft_id'] = $aircraftId;
}

$stmt = $pdo->prepare("
    SELECT
      sfi.id AS flight_instance_id,
      sfi.flight_code,
      sfi.status,
      sfi.dispatch_status,
      sfi.flight_operation_type,
      sfi.origin_airport_icao_code,
      sfi.destination_airport_icao_code,
      sfi.actual_departure_at_utc,
      sfi.scheduled_arrival_at_utc,
      sfi.actual_arrival_at_utc,
      sfi.passenger_capacity,
      sfi.passenger_count,
      sfi.passenger_revenue,
      sfi.total_operating_cost,
      sfi.profit_amount,
      sfi.currency_code,

      ca.id AS aircraft_id,
      ca.registration_code,
      ca.status AS aircraft_status,
      ca.current_airport_icao_code,

      am.model_code,
      am.icao_type_code,
      am.manufacturer,
      am.model_name,
      am.cruise_speed_kmh,
      am.range_km,

      p1.display_name AS pilot_1_name,
      p2.display_name AS pilot_2_name

    FROM scheduled_flight_instances sfi
    JOIN company_aircraft ca
      ON ca.id = sfi.aircraft_id
    JOIN aircraft_models am
      ON am.id = ca.aircraft_model_id
    LEFT JOIN company_staff p1
      ON p1.id = sfi.pilot_1_staff_id
    LEFT JOIN company_staff p2
      ON p2.id = sfi.pilot_2_staff_id
    WHERE sfi.company_id = :company_id
      AND {$where}
    ORDER BY sfi.id DESC
    LIMIT 1
");
$stmt->execute($params);

$flight = $stmt->fetch();

if (!$flight) {
    json_response([
        'error' => 'ACTIVE_FLIGHT_NOT_FOUND',
        'message' => 'No matching active flight was found.',
    ], 404);
}

$nowTs = time();
$departureTs = parse_utc_ts($flight['actual_departure_at_utc'] ?? null);
$arrivalTs = parse_utc_ts($flight['scheduled_arrival_at_utc'] ?? null);

$totalSeconds = ($departureTs && $arrivalTs && $arrivalTs > $departureTs)
    ? $arrivalTs - $departureTs
    : 0;

$remainingSeconds = ($arrivalTs)
    ? max(0, $arrivalTs - $nowTs)
    : null;

$elapsedSeconds = ($departureTs)
    ? max(0, $nowTs - $departureTs)
    : null;

$progressPercent = ($totalSeconds > 0 && $elapsedSeconds !== null)
    ? max(0, min(100, ($elapsedSeconds / $totalSeconds) * 100))
    : null;

json_response([
    'flight' => [
        'flight_instance_id' => (int)$flight['flight_instance_id'],
        'flight_code' => $flight['flight_code'],
        'status' => $flight['status'],
        'dispatch_status' => $flight['dispatch_status'],
        'flight_operation_type' => $flight['flight_operation_type'],
        'origin_airport_icao_code' => $flight['origin_airport_icao_code'],
        'destination_airport_icao_code' => $flight['destination_airport_icao_code'],
        'actual_departure_at_utc' => $flight['actual_departure_at_utc'],
        'scheduled_arrival_at_utc' => $flight['scheduled_arrival_at_utc'],
        'actual_arrival_at_utc' => $flight['actual_arrival_at_utc'],
        'remaining_seconds' => $remainingSeconds,
        'elapsed_seconds' => $elapsedSeconds,
        'total_seconds' => $totalSeconds,
        'progress_percent' => $progressPercent,
        'passenger_capacity' => (int)$flight['passenger_capacity'],
        'passenger_count' => (int)$flight['passenger_count'],
        'passenger_revenue' => $flight['passenger_revenue'],
        'total_operating_cost' => $flight['total_operating_cost'],
        'profit_amount' => $flight['profit_amount'],
        'currency_code' => $flight['currency_code'],
    ],
    'aircraft' => [
        'aircraft_id' => (int)$flight['aircraft_id'],
        'registration_code' => $flight['registration_code'],
        'aircraft_status' => $flight['aircraft_status'],
        'current_airport_icao_code' => $flight['current_airport_icao_code'],
        'model_code' => $flight['model_code'],
        'icao_type_code' => $flight['icao_type_code'],
        'manufacturer' => $flight['manufacturer'],
        'model_name' => $flight['model_name'],
        'cruise_speed_kmh' => $flight['cruise_speed_kmh'],
        'range_km' => $flight['range_km'],
    ],
    'crew' => [
        'pilot_1_name' => $flight['pilot_1_name'],
        'pilot_2_name' => $flight['pilot_2_name'],
    ],
]);

function parse_utc_ts(mixed $value): ?int
{
    if (!$value) {
        return null;
    }

    $ts = strtotime((string)$value . ' UTC');

    return $ts === false ? null : $ts;
}
