<?php
declare(strict_types=1);

require __DIR__ . '/../../lib/bootstrap.php';
require __DIR__ . '/../../lib/session.php';
require_once __DIR__ . '/../../lib/flight-completion.php';
require_once __DIR__ . '/../../lib/maintenance-engine.php';

$session = require_auth_session();
$companyId = (int)$session['company_id'];

$pdo = db();

complete_due_flights($pdo, $companyId);
complete_due_maintenance($pdo, $companyId);

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

      ca.id AS aircraft_id,
      ca.registration_code,
      ca.status AS aircraft_status,

      am.model_code,
      am.icao_type_code,
      am.manufacturer,
      am.model_name,
      am.cruise_speed_kmh,

      TIMESTAMPDIFF(SECOND, UTC_TIMESTAMP(), sfi.scheduled_arrival_at_utc) AS remaining_seconds
    FROM scheduled_flight_instances sfi
    JOIN company_aircraft ca
      ON ca.id = sfi.aircraft_id
    JOIN aircraft_models am
      ON am.id = ca.aircraft_model_id
    WHERE sfi.company_id = :company_id
      AND sfi.status = 'IN_FLIGHT'
    ORDER BY sfi.actual_departure_at_utc DESC, sfi.id DESC
");
$stmt->execute(['company_id' => $companyId]);

json_response([
    'active_flights' => $stmt->fetchAll(),
]);
