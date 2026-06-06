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

$columns = table_columns($pdo, 'scheduled_services');
$serviceTypeExpr = isset($columns['service_type'])
    ? "ss.service_type"
    : "CASE WHEN ss.scheduled_departure_time_utc IS NULL THEN 'ON_DEMAND' ELSE 'SCHEDULED' END AS service_type";
$compatibleModelsExpr = isset($columns['compatible_aircraft_model_codes'])
    ? "ss.compatible_aircraft_model_codes"
    : "'C208B_GRAND_CARAVAN_EX,PC12_NGX,DHC6_TWIN_OTTER_400,L410_NG' AS compatible_aircraft_model_codes";

$stmt = $pdo->prepare("
    SELECT
      ss.*,
      {$serviceTypeExpr},
      {$compatibleModelsExpr},
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

$service['compatible_aircraft_icao_codes'] = compatible_icao_codes(
    $pdo,
    (string)($service['compatible_aircraft_model_codes'] ?? '')
);

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

function compatible_icao_codes(PDO $pdo, string $modelCodesCsv): string
{
    $modelCodes = array_values(array_filter(array_map(
        static fn (string $value): string => trim($value),
        explode(',', $modelCodesCsv)
    )));

    if (!$modelCodes) {
        return 'C208';
    }

    $placeholders = implode(',', array_fill(0, count($modelCodes), '?'));

    $stmt = $pdo->prepare("
        SELECT model_code, icao_type_code
        FROM aircraft_models
        WHERE model_code IN ({$placeholders})
        ORDER BY FIELD(model_code, {$placeholders})
    ");

    $params = array_merge($modelCodes, $modelCodes);
    $stmt->execute($params);

    $codes = [];
    foreach ($stmt->fetchAll() as $row) {
        if (!empty($row['icao_type_code'])) {
            $codes[] = $row['icao_type_code'];
        }
    }

    return implode(', ', array_values(array_unique($codes)));
}

function table_columns(PDO $pdo, string $tableName): array
{
    $stmt = $pdo->prepare("
        SELECT COLUMN_NAME
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = :table_name
    ");
    $stmt->execute(['table_name' => $tableName]);

    return array_flip(array_map(static fn ($row) => $row['COLUMN_NAME'], $stmt->fetchAll()));
}
