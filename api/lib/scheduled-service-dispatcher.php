<?php
declare(strict_types=1);

require_once __DIR__ . '/flight-completion.php';
require_once __DIR__ . '/flight-dispatch-selection.php';
require_once __DIR__ . '/missed-scheduled-flight-penalty.php';

const ICARO_AUTO_DISPATCH_STATUS = 'AUTO_DISPATCHED_SCHEDULED';

/**
 * Process scheduled services that are due in UTC.
 *
 * Important:
 * - This function never starts future flights early.
 * - $windowMinutes is a look-back window for overdue services.
 * - Manual "start now" flights do not consume the daily automatic schedule.
 */
function process_due_scheduled_services(
    PDO $pdo,
    int $companyId,
    int $windowMinutes = 240,
    bool $devForce = false
): array {
    $windowMinutes = max(1, min(1440, $windowMinutes));

    complete_due_flights($pdo, $companyId);

    $services = icaro_fetch_due_scheduled_services($pdo, $companyId, $windowMinutes, $devForce);
    $results = [];

    foreach ($services as $serviceRow) {
        $serviceId = (int)$serviceRow['service_id'];
        $scheduledDeparture = (string)$serviceRow['scheduled_departure_at_utc'];
        $flightDateUtc = substr($scheduledDeparture, 0, 10);

        if (icaro_already_auto_processed_service_date($pdo, $companyId, $serviceId, $flightDateUtc)) {
            $results[] = [
                'service_id' => $serviceId,
                'result' => 'SKIPPED_ALREADY_AUTO_PROCESSED',
                'scheduled_departure_at_utc' => $scheduledDeparture,
            ];
            continue;
        }

        $service = dispatch_fetch_flight_definition_for_update($pdo, $companyId, $serviceId);

        if (!$service) {
            $results[] = [
                'service_id' => $serviceId,
                'result' => 'SKIPPED_SERVICE_NOT_FOUND',
            ];
            continue;
        }

        /*
         * The route-aware row has all fields needed by the automatic dispatcher.
         * Merge it with the existing shared dispatcher definition so older helpers
         * remain compatible.
         */
        $service = array_merge($serviceRow, $service);

        $aircraft = dispatch_choose_best_available_aircraft($pdo, $companyId, $service);

        if (!$aircraft) {
            apply_missed_scheduled_flight_penalty(
                $pdo,
                $companyId,
                $service,
                'No compatible available aircraft was present at the scheduled flight origin airport.'
            );

            $results[] = [
                'service_id' => $serviceId,
                'result' => 'MISSED_NO_AVAILABLE_AIRCRAFT',
                'scheduled_departure_at_utc' => $scheduledDeparture,
                'origin_airport_icao_code' => $service['origin_airport_icao_code'] ?? null,
            ];
            continue;
        }

        $pilots = dispatch_fetch_pilots_for_aircraft_model($pdo, $companyId, (string)$aircraft['model_code']);

        if (count($pilots) < 2) {
            $results[] = [
                'service_id' => $serviceId,
                'result' => 'BLOCKED_INSUFFICIENT_CREW',
                'available_pilots' => count($pilots),
                'scheduled_departure_at_utc' => $scheduledDeparture,
            ];
            continue;
        }

        $technician = dispatch_fetch_best_technician($pdo, $companyId);
        $flight = icaro_start_scheduled_service_flight(
            $pdo,
            $companyId,
            $service,
            $aircraft,
            $pilots,
            $technician,
            $scheduledDeparture,
            $flightDateUtc
        );

        $results[] = [
            'service_id' => $serviceId,
            'result' => 'DISPATCHED',
            'flight_instance_id' => $flight['flight_instance_id'],
            'flight_code' => $flight['flight_code'],
            'aircraft_id' => (int)$aircraft['aircraft_id'],
            'scheduled_departure_at_utc' => $scheduledDeparture,
        ];
    }

    complete_due_flights($pdo, $companyId);

    return [
        'status' => 'OK',
        'processed_count' => count($results),
        'results' => $results,
    ];
}

function icaro_fetch_due_scheduled_services(PDO $pdo, int $companyId, int $windowMinutes, bool $devForce): array
{
    $nowTs = time();
    $today = gmdate('Y-m-d', $nowTs);

    $stmt = $pdo->prepare("
        SELECT
          ss.id AS service_id,
          ss.company_id,
          ss.air_route_id,
          ss.service_code,
          ss.flight_route_code,
          ss.service_type,
          ss.recurrence_type,
          ss.scheduled_departure_time_utc,
          ss.service_status,
          ss.preferred_aircraft_model_id,
          ss.compatible_aircraft_model_codes,
          ss.required_aircraft_class AS service_required_aircraft_class,
          ss.base_ticket_price,
          ss.currency_code,
          ss.auto_dispatch_enabled,
          ss.allow_backup_aircraft,
          ss.allow_extra_flights,
          ar.route_code,
          ar.route_public_code,
          ar.origin_airport_icao_code,
          ar.destination_airport_icao_code,
          ar.required_aircraft_class,
          ar.planned_distance_km,
          ar.estimated_block_minutes
        FROM scheduled_services ss
        JOIN air_routes ar ON ar.id = ss.air_route_id
        WHERE ss.company_id = :company_id
          AND ss.service_status = 'ACTIVE'
          AND ar.status = 'ACTIVE'
          AND UPPER(COALESCE(ss.service_type, 'SCHEDULED')) = 'SCHEDULED'
          AND COALESCE(ss.auto_dispatch_enabled, 1) = 1
          AND ss.scheduled_departure_time_utc IS NOT NULL
        ORDER BY ss.scheduled_departure_time_utc, ss.id
    ");
    $stmt->execute(['company_id' => $companyId]);

    $due = [];

    foreach ($stmt->fetchAll() as $row) {
        $scheduledDeparture = $today . ' ' . (string)$row['scheduled_departure_time_utc'];
        $departureTs = strtotime($scheduledDeparture . ' UTC');

        if ($departureTs === false) {
            continue;
        }

        if (!$devForce && $departureTs > $nowTs) {
            continue;
        }

        if (!$devForce && $departureTs < ($nowTs - ($windowMinutes * 60))) {
            continue;
        }

        $row['scheduled_departure_at_utc'] = gmdate('Y-m-d H:i:s', $departureTs);
        $due[] = $row;
    }

    return $due;
}

/**
 * Manual "start now" flights must not consume the daily automatic schedule.
 */
function icaro_already_auto_processed_service_date(PDO $pdo, int $companyId, int $serviceId, string $flightDateUtc): bool
{
    $stmt = $pdo->prepare("
        SELECT COUNT(*)
        FROM scheduled_flight_instances
        WHERE company_id = :company_id
          AND scheduled_service_id = :service_id
          AND flight_date_utc = :flight_date_utc
          AND status <> 'CANCELLED'
          AND dispatch_status = :dispatch_status
    ");
    $stmt->execute([
        'company_id' => $companyId,
        'service_id' => $serviceId,
        'flight_date_utc' => $flightDateUtc,
        'dispatch_status' => ICARO_AUTO_DISPATCH_STATUS,
    ]);

    return (int)$stmt->fetchColumn() > 0;
}

function icaro_start_scheduled_service_flight(
    PDO $pdo,
    int $companyId,
    array $service,
    array $aircraft,
    array $pilots,
    ?array $technician,
    string $scheduledDeparture,
    string $flightDateUtc
): array {
    $flightCode = icaro_next_flight_instance_code($pdo, $companyId);
    $durationMinutes = max(20, (int)($service['estimated_block_minutes'] ?? 60));
    $actualDeparture = gmdate('Y-m-d H:i:s');
    $scheduledArrival = gmdate(
        'Y-m-d H:i:s',
        strtotime($scheduledDeparture . ' UTC') + ($durationMinutes * 60)
    );

    $capacity = max(1, (int)($aircraft['passenger_capacity_standard'] ?? 1));
    $loadFactor = random_int(55, 100);
    $passengerCount = min($capacity, max(1, (int)floor($capacity * $loadFactor / 100)));
    $ticketPrice = (float)($service['base_ticket_price'] ?? 0);
    $revenue = $passengerCount * $ticketPrice;
    $blockHours = $durationMinutes / 60.0;
    $fuelCost = $blockHours * (float)($aircraft['fuel_burn_kg_per_hour'] ?? 0) * 1.20;
    $maintenanceCost = $blockHours * (float)($aircraft['maintenance_cost_per_hour'] ?? 0);
    $staffCost = ((float)($pilots[0]['salary_per_flight'] ?? 0)) + ((float)($pilots[1]['salary_per_flight'] ?? 0));
    $operatingCost = $fuelCost + $maintenanceCost + $staffCost;
    $profit = $revenue - $operatingCost;

    $columns = icaro_table_columns($pdo, 'scheduled_flight_instances');
    $values = [];

    icaro_put($values, $columns, 'company_id', $companyId);
    icaro_put($values, $columns, 'air_route_id', (int)($service['air_route_id'] ?? 0));
    icaro_put($values, $columns, 'scheduled_service_id', (int)$service['service_id']);
    icaro_put($values, $columns, 'flight_code', $flightCode);
    icaro_put($values, $columns, 'flight_date_utc', $flightDateUtc);
    icaro_put($values, $columns, 'flight_operation_type', 'SCHEDULED');
    icaro_put($values, $columns, 'status', 'IN_FLIGHT');
    icaro_put($values, $columns, 'dispatch_status', ICARO_AUTO_DISPATCH_STATUS);
    icaro_put($values, $columns, 'backup_used', 0);
    icaro_put($values, $columns, 'origin_airport_icao_code', $service['origin_airport_icao_code']);
    icaro_put($values, $columns, 'destination_airport_icao_code', $service['destination_airport_icao_code']);
    icaro_put($values, $columns, 'required_aircraft_class', $service['required_aircraft_class'] ?? $service['service_required_aircraft_class'] ?? 'LIGHT_COMMERCIAL');
    icaro_put($values, $columns, 'preferred_aircraft_model_id', $service['preferred_aircraft_model_id'] ?? null);
    icaro_put($values, $columns, 'aircraft_id', (int)$aircraft['aircraft_id']);
    icaro_put($values, $columns, 'planned_aircraft_id', (int)$aircraft['aircraft_id']);
    icaro_put($values, $columns, 'dispatch_aircraft_id', (int)$aircraft['aircraft_id']);
    icaro_put($values, $columns, 'pilot_1_staff_id', (int)$pilots[0]['staff_id']);
    icaro_put($values, $columns, 'pilot_2_staff_id', (int)$pilots[1]['staff_id']);
    icaro_put($values, $columns, 'technician_staff_id', $technician ? (int)$technician['staff_id'] : null);
    icaro_put($values, $columns, 'passenger_capacity', $capacity);
    icaro_put($values, $columns, 'passenger_count', $passengerCount);
    icaro_put($values, $columns, 'load_factor_percent', number_format(($passengerCount / $capacity) * 100, 2, '.', ''));
    icaro_put($values, $columns, 'ticket_price', number_format($ticketPrice, 2, '.', ''));
    icaro_put($values, $columns, 'passenger_revenue', number_format($revenue, 2, '.', ''));
    icaro_put($values, $columns, 'fuel_cost', number_format($fuelCost, 2, '.', ''));
    icaro_put($values, $columns, 'maintenance_cost', number_format($maintenanceCost, 2, '.', ''));
    icaro_put($values, $columns, 'staff_cost', number_format($staffCost, 2, '.', ''));
    icaro_put($values, $columns, 'total_operating_cost', number_format($operatingCost, 2, '.', ''));
    icaro_put($values, $columns, 'profit_amount', number_format($profit, 2, '.', ''));
    icaro_put($values, $columns, 'currency_code', $service['currency_code'] ?? 'EUR');
    icaro_put($values, $columns, 'scheduled_departure_at_utc', $scheduledDeparture);
    icaro_put($values, $columns, 'actual_departure_at_utc', $actualDeparture);
    icaro_put($values, $columns, 'scheduled_arrival_at_utc', $scheduledArrival);
    icaro_put($values, $columns, 'actual_arrival_at_utc', null);

    $flightInstanceId = icaro_insert_dynamic($pdo, 'scheduled_flight_instances', $values);

    $pdo->prepare("
        UPDATE company_aircraft
        SET status = 'IN_FLIGHT',
            current_airport_icao_code = :destination
        WHERE id = :aircraft_id
          AND company_id = :company_id
    ")->execute([
        'destination' => $service['destination_airport_icao_code'],
        'aircraft_id' => (int)$aircraft['aircraft_id'],
        'company_id' => $companyId,
    ]);

    return [
        'flight_instance_id' => $flightInstanceId,
        'flight_code' => $flightCode,
    ];
}

function icaro_next_flight_instance_code(PDO $pdo, int $companyId): string
{
    $base = time();
    $candidate = 'IO-' . $base;
    $suffix = 0;
    $stmt = $pdo->prepare("
        SELECT COUNT(*)
        FROM scheduled_flight_instances
        WHERE company_id = :company_id
          AND flight_code = :flight_code
    ");

    while (true) {
        $code = $suffix === 0 ? $candidate : $candidate . '-' . $suffix;
        $stmt->execute([
            'company_id' => $companyId,
            'flight_code' => $code,
        ]);

        if ((int)$stmt->fetchColumn() === 0) {
            return $code;
        }

        $suffix++;
    }
}

function icaro_table_columns(PDO $pdo, string $tableName): array
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

function icaro_put(array &$values, array $columns, string $column, mixed $value): void
{
    if (isset($columns[$column])) {
        $values[$column] = $value;
    }
}

function icaro_insert_dynamic(PDO $pdo, string $tableName, array $values): int
{
    $columns = array_keys($values);
    $quoted = array_map(static fn ($column) => "`{$column}`", $columns);
    $placeholders = array_map(static fn ($column) => ":{$column}", $columns);

    $sql = "INSERT INTO {$tableName} (" . implode(', ', $quoted) . ") VALUES (" . implode(', ', $placeholders) . ")";
    $stmt = $pdo->prepare($sql);

    foreach ($values as $column => $value) {
        $stmt->bindValue(":{$column}", $value);
    }

    $stmt->execute();

    return (int)$pdo->lastInsertId();
}
