<?php
declare(strict_types=1);

require __DIR__ . '/../../lib/bootstrap.php';
require __DIR__ . '/../../lib/aircraft-images.php';
require __DIR__ . '/../../lib/session.php';

$session = require_auth_session();
$companyId = (int)$session['company_id'];
$aircraftId = filter_input(INPUT_GET, 'aircraftId', FILTER_VALIDATE_INT);

if (!$aircraftId) {
    json_response(['error' => 'INVALID_AIRCRAFT_ID'], 422);
}

$pdo = db();

$stmt = $pdo->prepare("
    SELECT
      ca.id AS aircraft_id,
      ca.*,
      am.manufacturer,
      am.model_name,
      am.model_code,
      am.icao_type_code,
      am.operation_role,
      am.passenger_capacity_standard,
      am.range_km,
      am.cruise_speed_kmh,
      am.fuel_burn_kg_per_hour,
      am.maintenance_cost_per_hour,
      am.image_asset_path
    FROM company_aircraft ca
    JOIN aircraft_models am
      ON am.id = ca.aircraft_model_id
    WHERE ca.company_id = :company_id
      AND ca.id = :aircraft_id
    LIMIT 1
");
$stmt->execute([
    'company_id' => $companyId,
    'aircraft_id' => $aircraftId,
]);
$aircraft = $stmt->fetch();

if (!$aircraft) {
    json_response(['error' => 'AIRCRAFT_NOT_FOUND'], 404);
}

$aircraft = attach_aircraft_image_asset_path($aircraft);

$flightStmt = $pdo->prepare("
    SELECT
      id,
      flight_code,
      status,
      origin_airport_icao_code,
      destination_airport_icao_code,
      profit_amount,
      currency_code,
      actual_departure_at_utc,
      actual_arrival_at_utc
    FROM scheduled_flight_instances
    WHERE company_id = :company_id
      AND aircraft_id = :aircraft_id
    ORDER BY id DESC
    LIMIT 10
");
$flightStmt->execute([
    'company_id' => $companyId,
    'aircraft_id' => $aircraftId,
]);

json_response([
    'aircraft' => $aircraft,
    'recent_flights' => $flightStmt->fetchAll(),
]);
