<?php
declare(strict_types=1);

require __DIR__ . '/../../lib/bootstrap.php';
require __DIR__ . '/../../lib/session.php';

$session = require_auth_session();
$companyId = (int)$session['company_id'];

$pdo = db();

$stmt = $pdo->prepare("
    SELECT
      am.id AS aircraft_model_id,
      am.model_code,
      am.icao_type_code,
      am.manufacturer,
      am.model_name,
      am.operation_role,
      am.passenger_capacity_standard,
      am.range_km,
      am.cruise_speed_kmh,
      COUNT(ca.id) AS owned_count,
      SUM(CASE WHEN ca.status IN ('AVAILABLE', 'PARKED') THEN 1 ELSE 0 END) AS available_count,
      GROUP_CONCAT(ca.registration_code ORDER BY ca.registration_code SEPARATOR ', ') AS registrations
    FROM company_aircraft ca
    JOIN aircraft_models am
      ON am.id = ca.aircraft_model_id
    WHERE ca.company_id = :company_id
    GROUP BY
      am.id,
      am.model_code,
      am.icao_type_code,
      am.manufacturer,
      am.model_name,
      am.operation_role,
      am.passenger_capacity_standard,
      am.range_km,
      am.cruise_speed_kmh
    ORDER BY
      am.manufacturer,
      am.model_name
");
$stmt->execute(['company_id' => $companyId]);

json_response([
    'models' => $stmt->fetchAll(),
]);
