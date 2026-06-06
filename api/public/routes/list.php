<?php
declare(strict_types=1);

require __DIR__ . '/../../lib/bootstrap.php';
require __DIR__ . '/../../lib/session.php';

$session = require_auth_session();
$companyId = (int)$session['company_id'];

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
      ss.id AS service_id,
      ss.id AS route_id,
      ss.service_code,
      {$serviceTypeExpr},
      ss.company_id,
      ss.air_route_id,
      ss.recurrence_type,
      ss.scheduled_departure_time_utc,
      ss.service_status AS status,
      ss.required_aircraft_class,
      ss.preferred_aircraft_model_id,
      {$compatibleModelsExpr},
      ss.base_ticket_price AS ticket_price,
      ss.currency_code,
      ss.auto_dispatch_enabled,
      ss.allow_backup_aircraft,
      ss.allow_extra_flights,

      ar.route_code,
      ar.origin_airport_icao_code,
      ar.destination_airport_icao_code,
      ar.route_scope,
      ar.route_market,
      ar.route_operation_domain,
      ar.planned_distance_km,
      ar.estimated_block_minutes AS planned_duration_minutes,

      oa.name AS origin_airport_name,
      da.name AS destination_airport_name,

      am.manufacturer,
      am.model_name,
      am.model_code,
      am.icao_type_code,

      (
        SELECT COUNT(*)
        FROM scheduled_flight_instances f
        WHERE f.company_id = ss.company_id
          AND f.scheduled_service_id = ss.id
      ) AS generated_flights_count,

      (
        SELECT COUNT(*)
        FROM scheduled_flight_instances f
        WHERE f.company_id = ss.company_id
          AND f.scheduled_service_id = ss.id
          AND f.status = 'IN_FLIGHT'
      ) AS active_flights_count
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
      AND ss.service_status <> 'CANCELLED'
    ORDER BY
      CASE
        WHEN ss.scheduled_departure_time_utc IS NULL THEN '99:99:99'
        ELSE ss.scheduled_departure_time_utc
      END,
      ar.origin_airport_icao_code,
      ar.destination_airport_icao_code
");
$stmt->execute(['company_id' => $companyId]);

$rows = $stmt->fetchAll();

foreach ($rows as &$row) {
    $row['compatible_aircraft_icao_codes'] = compatible_icao_codes(
        $pdo,
        (string)($row['compatible_aircraft_model_codes'] ?? '')
    );
}
unset($row);

json_response($rows);

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
