<?php
declare(strict_types=1);

function dispatch_fetch_flight_definition_for_update(PDO $pdo, int $companyId, int $serviceId): ?array
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
          ss.currency_code,
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
        FOR UPDATE
    ");
    $stmt->execute(['company_id' => $companyId, 'service_id' => $serviceId]);
    $row = $stmt->fetch();
    return $row ?: null;
}

function dispatch_fetch_specific_available_aircraft(PDO $pdo, int $companyId, array $service, int $aircraftId): ?array
{
    $sql = dispatch_available_aircraft_sql($service, true);
    $params = dispatch_available_aircraft_params($companyId, $service);
    $params['aircraft_id'] = $aircraftId;
    $stmt = $pdo->prepare($sql);
    $stmt->execute($params);
    $row = $stmt->fetch();
    return $row ?: null;
}

function dispatch_choose_best_available_aircraft(PDO $pdo, int $companyId, array $service): ?array
{
    $sql = dispatch_available_aircraft_sql($service, false) . "
        ORDER BY estimated_profit_score DESC, ca.condition_percent DESC, ca.registration_code
        LIMIT 1
    ";
    $stmt = $pdo->prepare($sql);
    $stmt->execute(dispatch_available_aircraft_params($companyId, $service));
    $row = $stmt->fetch();
    return $row ?: null;
}

function dispatch_available_aircraft_sql(array $service, bool $specific): string
{
    $allowed = dispatch_allowed_model_codes($service);
    $sql = "
        SELECT
          ca.id AS aircraft_id,
          ca.registration_code,
          ca.status,
          ca.home_base_icao_code,
          ca.current_airport_icao_code,
          ca.condition_percent,
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
    if ($specific) {
        $sql .= " AND ca.id = :aircraft_id";
    }
    if ($allowed) {
        $placeholders = [];
        foreach ($allowed as $index => $code) {
            $placeholders[] = ':model_code_' . $index;
        }
        $sql .= " AND am.model_code IN (" . implode(',', $placeholders) . ")";
    }
    return $sql;
}

function dispatch_available_aircraft_params(int $companyId, array $service): array
{
    $params = [
        'company_id' => $companyId,
        'origin' => $service['origin_airport_icao_code'],
        'ticket_price' => (float)($service['base_ticket_price'] ?? 0),
        'block_minutes' => (int)($service['estimated_block_minutes'] ?? 60),
    ];
    foreach (dispatch_allowed_model_codes($service) as $index => $code) {
        $params['model_code_' . $index] = $code;
    }
    return $params;
}

function dispatch_allowed_model_codes(array $service): array
{
    return array_values(array_filter(array_map(
        static fn (string $value): string => trim($value),
        explode(',', (string)($service['compatible_aircraft_model_codes'] ?? ''))
    )));
}

function dispatch_fetch_pilots_for_aircraft_model(PDO $pdo, int $companyId, string $modelCode): array
{
    $license = match ($modelCode) {
        'C208B_GRAND_CARAVAN_EX' => 'C208_TYPE',
        'DHC6_TWIN_OTTER_400' => 'DHC6_TYPE',
        'ATR42_600' => 'ATR42_TYPE',
        default => null,
    };

    $sql = "
        SELECT s.id AS staff_id, s.display_name, s.salary_per_flight
        FROM company_staff s
        WHERE s.company_id = :company_id
          AND s.staff_role = 'PILOT'
          AND s.employment_status = 'ACTIVE'
          AND EXISTS (
            SELECT 1 FROM company_staff_licenses l
            WHERE l.company_staff_id = s.id AND l.license_code = 'CPL'
          )
    ";
    $params = ['company_id' => $companyId];

    if ($license !== null) {
        $sql .= "
          AND EXISTS (
            SELECT 1 FROM company_staff_licenses l
            WHERE l.company_staff_id = s.id AND l.license_code = :license
          )
        ";
        $params['license'] = $license;
    }

    $sql .= " ORDER BY s.reliability_score DESC, s.fatigue_score ASC, s.id LIMIT 2";
    $stmt = $pdo->prepare($sql);
    $stmt->execute($params);
    return $stmt->fetchAll();
}

function dispatch_fetch_best_technician(PDO $pdo, int $companyId): ?array
{
    $stmt = $pdo->prepare("
        SELECT s.id AS staff_id, s.display_name
        FROM company_staff s
        WHERE s.company_id = :company_id
          AND s.staff_role = 'TECHNICIAN'
          AND s.employment_status = 'ACTIVE'
        ORDER BY s.reliability_score DESC, s.fatigue_score ASC, s.id
        LIMIT 1
    ");
    $stmt->execute(['company_id' => $companyId]);
    $row = $stmt->fetch();
    return $row ?: null;
}
