<?php
declare(strict_types=1);

require __DIR__ . '/../../lib/bootstrap.php';
require __DIR__ . '/../../lib/session.php';

$session = require_auth_session();
$companyId = (int)$session['company_id'];
$serviceId = filter_input(INPUT_GET, 'service_id', FILTER_VALIDATE_INT);

if (!$serviceId) {
    json_response(['error' => 'INVALID_FLIGHT_ID'], 422);
}

$pdo = db();
$service = fetch_flight_definition($pdo, $companyId, $serviceId);

if (!$service) {
    json_response(['error' => 'FLIGHT_NOT_FOUND'], 404);
}

json_response([
    'flight' => [
        'service_id' => (int)$service['service_id'],
        'flight_code' => $service['flight_route_code'] ?: $service['service_code'],
        'service_type' => $service['service_type'],
        'origin_airport_icao_code' => $service['origin_airport_icao_code'],
        'destination_airport_icao_code' => $service['destination_airport_icao_code'],
        'compatible_aircraft_model_codes' => $service['compatible_aircraft_model_codes'],
    ],
    'available_aircraft' => fetch_available_aircraft_for_flight($pdo, $companyId, $service),
]);

function fetch_flight_definition(PDO $pdo, int $companyId, int $serviceId): ?array
{
    $stmt = $pdo->prepare("
        SELECT
          ss.id AS service_id,
          ss.company_id,
          ss.service_code,
          ss.flight_route_code,
          ss.service_type,
          ss.compatible_aircraft_model_codes,
          ss.preferred_aircraft_model_id,
          ss.base_ticket_price,
          ar.origin_airport_icao_code,
          ar.destination_airport_icao_code,
          ar.planned_distance_km,
          ar.estimated_block_minutes
        FROM scheduled_services ss
        JOIN air_routes ar ON ar.id = ss.air_route_id
        WHERE ss.company_id = :company_id
          AND ss.id = :service_id
          AND ss.service_status <> 'CANCELLED'
        LIMIT 1
    ");
    $stmt->execute(['company_id' => $companyId, 'service_id' => $serviceId]);
    $row = $stmt->fetch();
    return $row ?: null;
}

function fetch_available_aircraft_for_flight(PDO $pdo, int $companyId, array $service): array
{
    $allowedModelCodes = normalize_model_codes((string)($service['compatible_aircraft_model_codes'] ?? ''));

    $sql = "
        SELECT
          ca.id AS company_aircraft_id,
          ca.id AS aircraft_id,
          ca.registration_code,
          ca.status,
          ca.home_base_icao_code,
          ca.current_airport_icao_code,
          ca.condition_percent,
          ca.airframe_hours,
          ca.cycles_count,
          am.id AS aircraft_model_id,
          am.model_code,
          am.icao_type_code,
          am.manufacturer,
          am.model_name,
          am.passenger_capacity_standard,
          am.range_km,
          am.cruise_speed_kmh,
          am.fuel_burn_kg_per_hour,
          am.maintenance_cost_per_hour,
          (
            COALESCE(am.passenger_capacity_standard, 0) * COALESCE(:ticket_price, 0)
            - (
              (COALESCE(:block_minutes, 60) / 60.0)
              * (
                COALESCE(am.fuel_burn_kg_per_hour, 0) * 1.20
                + COALESCE(am.maintenance_cost_per_hour, 0)
              )
            )
          ) AS estimated_profit_score
        FROM company_aircraft ca
        JOIN aircraft_models am ON am.id = ca.aircraft_model_id
        WHERE ca.company_id = :company_id
          AND ca.current_airport_icao_code = :origin
          AND ca.status IN ('AVAILABLE', 'PARKED')
          AND ca.condition_percent > 45.00
    ";

    $params = [
        'company_id' => $companyId,
        'origin' => $service['origin_airport_icao_code'],
        'ticket_price' => (float)($service['base_ticket_price'] ?? 0),
        'block_minutes' => (int)($service['estimated_block_minutes'] ?? 60),
    ];

    if ($allowedModelCodes) {
        $placeholders = [];
        foreach ($allowedModelCodes as $index => $modelCode) {
            $key = 'model_code_' . $index;
            $placeholders[] = ':' . $key;
            $params[$key] = $modelCode;
        }
        $sql .= " AND am.model_code IN (" . implode(',', $placeholders) . ")";
    }

    $sql .= " ORDER BY estimated_profit_score DESC, ca.condition_percent DESC, ca.registration_code";

    $stmt = $pdo->prepare($sql);
    $stmt->execute($params);
    return $stmt->fetchAll();
}

function normalize_model_codes(string $csv): array
{
    return array_values(array_filter(array_map(
        static fn (string $value): string => trim($value),
        explode(',', $csv)
    )));
}
