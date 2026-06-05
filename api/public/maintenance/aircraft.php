<?php
declare(strict_types=1);

require __DIR__ . '/../../lib/bootstrap.php';
require __DIR__ . '/../../lib/session.php';

$session = require_auth_session();
$companyId = $session['company_id'];
$aircraftId = filter_input(INPUT_GET, 'aircraftId', FILTER_VALIDATE_INT);

if (!$aircraftId) {
    json_response(['error' => 'INVALID_AIRCRAFT_ID'], 422);
}

$stmt = db()->prepare("
    SELECT *
    FROM v_company_aircraft_maintenance_detail
    WHERE company_id = :company_id
      AND aircraft_id = :aircraft_id
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

$eventsStmt = db()->prepare("
    SELECT
      e.id AS event_id,
      e.event_type,
      e.severity,
      e.status,
      e.title,
      e.description,
      e.condition_percent_before,
      e.condition_percent_after,
      e.required_technician_license,
      e.started_at_utc,
      e.estimated_completed_at_utc,
      e.completed_at_utc
    FROM aircraft_operational_events e
    WHERE e.company_id = :company_id
      AND e.aircraft_id = :aircraft_id
    ORDER BY e.started_at_utc DESC
    LIMIT 50
");
$eventsStmt->execute([
    'company_id' => $companyId,
    'aircraft_id' => $aircraftId,
]);

json_response([
    'aircraft' => [
        'aircraft_id' => (int)$aircraft['aircraft_id'],
        'company_id' => (int)$aircraft['company_id'],
        'registration_code' => $aircraft['registration_code'],
        'serial_number' => $aircraft['serial_number'],
        'manufacture_year' => (int)$aircraft['manufacture_year'],
        'manufacturer' => $aircraft['manufacturer'],
        'model_name' => $aircraft['model_name'],
        'model_code' => $aircraft['model_code'],
        'icao_type_code' => $aircraft['icao_type_code'],
        'image_asset_path' => $aircraft['image_asset_path'],
        'aircraft_status' => $aircraft['aircraft_status'],
        'maintenance_state' => $aircraft['maintenance_state'],
        'home_base_icao_code' => $aircraft['home_base_icao_code'],
        'home_base_name' => $aircraft['home_base_name'],
        'current_airport_icao_code' => $aircraft['current_airport_icao_code'],
        'current_airport_name' => $aircraft['current_airport_name'],
        'condition_percent' => $aircraft['condition_percent'],
        'airframe_hours' => $aircraft['airframe_hours'],
        'cycles_count' => (int)$aircraft['cycles_count'],
        'routine_maintenance_interval_hours' => (int)$aircraft['routine_maintenance_interval_hours'],
        'routine_maintenance_interval_cycles' => (int)$aircraft['routine_maintenance_interval_cycles'],
        'condition_warning_threshold_percent' => $aircraft['condition_warning_threshold_percent'],
        'condition_grounding_threshold_percent' => $aircraft['condition_grounding_threshold_percent'],
        'routine_maintenance_duration_hours' => (int)$aircraft['routine_maintenance_duration_hours'],
        'technician_license_required' => $aircraft['technician_license_required'],
        'open_event_count' => (int)$aircraft['open_event_count'],
        'currency_code' => $aircraft['currency_code'],
        'current_market_value' => $aircraft['current_market_value'],
    ],
    'events' => array_map(static function (array $row): array {
        return [
            'event_id' => (int)$row['event_id'],
            'event_type' => $row['event_type'],
            'severity' => $row['severity'],
            'status' => $row['status'],
            'title' => $row['title'],
            'description' => $row['description'],
            'condition_percent_before' => $row['condition_percent_before'],
            'condition_percent_after' => $row['condition_percent_after'],
            'required_technician_license' => $row['required_technician_license'],
            'started_at_utc' => $row['started_at_utc'],
            'estimated_completed_at_utc' => $row['estimated_completed_at_utc'],
            'completed_at_utc' => $row['completed_at_utc'],
        ];
    }, $eventsStmt->fetchAll()),
]);
