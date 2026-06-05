<?php
declare(strict_types=1);

require __DIR__ . '/../../lib/bootstrap.php';
require __DIR__ . '/../../lib/session.php';

$session = require_auth_session();
$companyId = (int)$session['company_id'];
$serviceId = filter_input(INPUT_GET, 'serviceId', FILTER_VALIDATE_INT);
$routeId = filter_input(INPUT_GET, 'routeId', FILTER_VALIDATE_INT);

$id = $serviceId ?: $routeId;

if (!$id) {
    json_response(['error' => 'INVALID_SERVICE_ID'], 422);
}

$pdo = db();

$stmt = $pdo->prepare("
    SELECT
      ss.*,
      ar.route_code,
      ar.origin_airport_icao_code,
      ar.destination_airport_icao_code,
      ar.route_scope,
      ar.route_market,
      ar.route_operation_domain,
      ar.planned_distance_km,
      ar.estimated_block_minutes,
      oa.name AS origin_airport_name,
      da.name AS destination_airport_name,
      am.manufacturer,
      am.model_name,
      am.model_code,
      am.icao_type_code
    FROM scheduled_services ss
    JOIN air_routes ar
      ON ar.id = ss.air_route_id
    LEFT JOIN airports oa
      ON oa.icao_code = ar.origin_airport_icao_code
    LEFT JOIN airports da
      ON da.icao_code = ar.destination_airport_icao_code
    LEFT JOIN aircraft_models am
      ON am.id = ss.preferred_aircraft_model_id
    WHERE ss.company_id = :company_id
      AND ss.id = :service_id
    LIMIT 1
");
$stmt->execute([
    'company_id' => $companyId,
    'service_id' => $id,
]);

$service = $stmt->fetch();

if (!$service) {
    json_response(['error' => 'SERVICE_NOT_FOUND'], 404);
}

$flightsStmt = $pdo->prepare("
    SELECT
      id,
      flight_code,
      flight_operation_type,
      status,
      dispatch_status,
      backup_used,
      aircraft_id,
      passenger_count,
      passenger_revenue,
      total_operating_cost,
      profit_amount,
      currency_code,
      scheduled_departure_at_utc,
      actual_departure_at_utc,
      scheduled_arrival_at_utc,
      actual_arrival_at_utc
    FROM scheduled_flight_instances
    WHERE company_id = :company_id
      AND scheduled_service_id = :service_id
    ORDER BY id DESC
    LIMIT 20
");
$flightsStmt->execute([
    'company_id' => $companyId,
    'service_id' => $id,
]);

json_response([
    'service' => $service,
    'recent_flights' => $flightsStmt->fetchAll(),
]);
