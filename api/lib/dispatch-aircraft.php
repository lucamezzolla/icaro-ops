<?php
declare(strict_types=1);

/**
 * Dispatch aircraft compatibility helper.
 *
 * Flights should not be permanently bound to an aircraft. At departure time,
 * the dispatch engine chooses a compatible available aircraft at the origin.
 */

function find_compatible_aircraft_for_flight(
    PDO $pdo,
    int $companyId,
    string $originAirportIcao,
    array $requirements
): ?array {
    $requiredClass = $requirements['required_aircraft_class'] ?? 'LIGHT_COMMERCIAL';
    $preferredModelId = isset($requirements['preferred_aircraft_model_id'])
        ? (int)$requirements['preferred_aircraft_model_id']
        : null;
    $requiredModelId = isset($requirements['required_aircraft_model_id'])
        ? (int)$requirements['required_aircraft_model_id']
        : null;
    $minRangeKm = isset($requirements['min_range_km']) ? (float)$requirements['min_range_km'] : 0.0;
    $minPassengerCapacity = isset($requirements['min_passenger_capacity']) ? (int)$requirements['min_passenger_capacity'] : 1;
    $maxPassengerCapacity = isset($requirements['max_passenger_capacity']) ? (int)$requirements['max_passenger_capacity'] : null;
    $allowedModelCodes = $requirements['allowed_model_codes'] ?? [];

    if (is_string($allowedModelCodes)) {
        $allowedModelCodes = array_values(array_filter(array_map('trim', explode(',', $allowedModelCodes))));
    }

    if (!is_array($allowedModelCodes)) {
        $allowedModelCodes = [];
    }

    $sql = "
        SELECT
          ca.id AS aircraft_id,
          ca.registration_code,
          ca.status,
          ca.current_airport_icao_code,
          ca.condition_percent,
          ca.airframe_hours,
          ca.cycles_count,
          am.id AS aircraft_model_id,
          am.manufacturer,
          am.model_name,
          am.model_code,
          am.icao_type_code,
          am.operation_role,
          am.passenger_capacity_standard,
          am.range_km,
          am.cruise_speed_kmh,
          CASE
            WHEN :preferred_model_id_check IS NOT NULL AND am.id = :preferred_model_id_match THEN 1
            WHEN :required_model_id_check IS NOT NULL AND am.id = :required_model_id_match THEN 2
            ELSE 3
          END AS dispatch_priority
        FROM company_aircraft ca
        JOIN aircraft_models am
          ON am.id = ca.aircraft_model_id
        WHERE ca.company_id = :company_id
          AND ca.current_airport_icao_code = :origin
          AND ca.status IN ('AVAILABLE', 'PARKED')
          AND ca.condition_percent > 45.00
          AND am.range_km >= :min_range_km
          AND am.passenger_capacity_standard >= :min_passenger_capacity
    ";

    $params = [
        'preferred_model_id_check' => $preferredModelId,
        'preferred_model_id_match' => $preferredModelId,
        'required_model_id_check' => $requiredModelId,
        'required_model_id_match' => $requiredModelId,
        'company_id' => $companyId,
        'origin' => $originAirportIcao,
        'min_range_km' => $minRangeKm,
        'min_passenger_capacity' => $minPassengerCapacity,
    ];

    if ($requiredModelId) {
        $sql .= " AND am.id = :required_model_filter";
        $params['required_model_filter'] = $requiredModelId;
    }

    if ($maxPassengerCapacity !== null) {
        $sql .= " AND am.passenger_capacity_standard <= :max_passenger_capacity";
        $params['max_passenger_capacity'] = $maxPassengerCapacity;
    }

    $sql .= compatible_aircraft_class_sql($requiredClass);

    $sql .= "
        ORDER BY
          dispatch_priority,
          ca.condition_percent DESC,
          ca.airframe_hours ASC,
          ca.id ASC
        LIMIT 1
    ";

    $stmt = $pdo->prepare($sql);
    $stmt->execute($params);
    $aircraft = $stmt->fetch();

    return $aircraft ?: null;
}

function compatible_aircraft_class_sql(string $requiredClass): string
{
    return match ($requiredClass) {
        'LIGHT_COMMERCIAL' => "
          AND am.model_code IN (
            'C208B_GRAND_CARAVAN_EX',
            'PC12_NGX',
            'DHC6_TWIN_OTTER_400',
            'L410_NG'
          )
        ",
        'REGIONAL_TURBOPROP' => "
          AND am.model_code IN (
            'ATR42_600',
            'SAAB_340B',
            'EMB120ER_BRASILIA',
            'DHC6_TWIN_OTTER_400',
            'L410_NG'
          )
        ",
        'HELICOPTER' => "
          AND am.operation_role LIKE '%HELICOPTER%'
        ",
        default => "",
    };
}

function dispatch_flight_aircraft(PDO $pdo, int $flightId, int $companyId): array
{
    $stmt = $pdo->prepare("
        SELECT
          f.id,
          f.origin_airport_icao_code,
          f.required_aircraft_class,
          f.preferred_aircraft_model_id,
          f.planned_aircraft_id,
          f.planned_distance_km
        FROM scheduled_flight_instances f
        WHERE f.id = :flight_id
          AND f.company_id = :company_id
        LIMIT 1
        FOR UPDATE
    ");
    $stmt->execute([
        'flight_id' => $flightId,
        'company_id' => $companyId,
    ]);

    $flight = $stmt->fetch();

    if (!$flight) {
        return ['status' => 'FLIGHT_NOT_FOUND', 'aircraft' => null];
    }

    $aircraft = find_compatible_aircraft_for_flight(
        $pdo,
        $companyId,
        (string)$flight['origin_airport_icao_code'],
        [
            'required_aircraft_class' => $flight['required_aircraft_class'] ?: 'LIGHT_COMMERCIAL',
            'preferred_aircraft_model_id' => $flight['preferred_aircraft_model_id'],
            'min_range_km' => $flight['planned_distance_km'] ?? 0,
            'min_passenger_capacity' => 1,
            'max_passenger_capacity' => 19,
        ]
    );

    if (!$aircraft) {
        $pdo->prepare("
            UPDATE scheduled_flight_instances
            SET
              dispatch_status = 'NO_COMPATIBLE_AIRCRAFT',
              schedule_conflict_status = CASE
                WHEN schedule_conflict_status = 'NONE' THEN 'CONFLICTED'
                ELSE schedule_conflict_status
              END
            WHERE id = :flight_id
              AND company_id = :company_id
        ")->execute([
            'flight_id' => $flightId,
            'company_id' => $companyId,
        ]);

        return ['status' => 'NO_COMPATIBLE_AIRCRAFT', 'aircraft' => null];
    }

    $backupUsed = (int)$aircraft['aircraft_id'] !== (int)($flight['planned_aircraft_id'] ?? 0);

    $pdo->prepare("
        UPDATE scheduled_flight_instances
        SET
          aircraft_id = :aircraft_id,
          dispatch_aircraft_id = :aircraft_id,
          dispatch_status = 'ASSIGNED',
          backup_used = :backup_used,
          backup_reason = CASE
            WHEN :backup_used = 1 THEN 'Compatible backup aircraft selected at departure airport.'
            ELSE backup_reason
          END
        WHERE id = :flight_id
          AND company_id = :company_id
    ")->execute([
        'aircraft_id' => (int)$aircraft['aircraft_id'],
        'backup_used' => $backupUsed ? 1 : 0,
        'flight_id' => $flightId,
        'company_id' => $companyId,
    ]);

    return [
        'status' => $backupUsed ? 'BACKUP_ASSIGNED' : 'ASSIGNED',
        'aircraft' => $aircraft,
    ];
}
