<?php
declare(strict_types=1);

require __DIR__ . '/../../lib/bootstrap.php';
require __DIR__ . '/../../lib/session.php';

$session = require_auth_session();
$companyId = (int)$session['company_id'];
$flightId = filter_input(INPUT_GET, 'flightId', FILTER_VALIDATE_INT);

if (!$flightId) {
    json_response(['error' => 'INVALID_FLIGHT_ID'], 422);
}

$pdo = db();

$stmt = $pdo->prepare("
    SELECT
      f.*,
      ca.registration_code, ca.serial_number, ca.manufacture_year, ca.ownership_status,
      ca.current_airport_icao_code AS aircraft_current_airport_icao_code,
      am.manufacturer, am.model_name, am.model_code, am.icao_type_code, am.operation_role,
      am.passenger_capacity_standard, am.cruise_speed_kmh, am.range_km,
      am.fuel_burn_kg_per_hour, am.maintenance_cost_per_hour,
      oa.name AS origin_airport_name, oa.city AS origin_city,
      da.name AS destination_airport_name, da.city AS destination_city,
      r.scheduled_departure_time_utc, r.planned_distance_km, r.planned_duration_minutes,
      r.recurrence_type, r.auto_dispatch_enabled, r.allow_backup_aircraft
    FROM scheduled_flight_instances f
    LEFT JOIN company_aircraft ca ON ca.id = f.aircraft_id
    LEFT JOIN aircraft_models am ON am.id = ca.aircraft_model_id
    LEFT JOIN airports oa ON oa.icao_code = f.origin_airport_icao_code
    LEFT JOIN airports da ON da.icao_code = f.destination_airport_icao_code
    LEFT JOIN company_routes r ON r.id = f.route_id
    WHERE f.company_id = :company_id
      AND f.id = :flight_id
    LIMIT 1
");
$stmt->execute([
    'company_id' => $companyId,
    'flight_id' => $flightId,
]);

$flight = $stmt->fetch();

if (!$flight) {
    json_response(['error' => 'FLIGHT_NOT_FOUND'], 404);
}

$repStmt = $pdo->prepare("
    SELECT event_code, reputation_before, reputation_delta, reputation_after, reason, created_at_utc
    FROM reputation_journal
    WHERE company_id = :company_id
      AND related_entity_type = 'FLIGHT'
      AND related_entity_id = :flight_id
    ORDER BY created_at_utc DESC, id DESC
");
$repStmt->execute([
    'company_id' => $companyId,
    'flight_id' => $flightId,
]);

json_response([
    'flight' => $flight,
    'reputation_journal' => array_map(static function (array $row): array {
        return [
            'event_code' => $row['event_code'],
            'reputation_before' => (int)$row['reputation_before'],
            'reputation_delta' => (int)$row['reputation_delta'],
            'reputation_after' => (int)$row['reputation_after'],
            'reason' => $row['reason'],
            'created_at_utc' => $row['created_at_utc'],
        ];
    }, $repStmt->fetchAll()),
]);
