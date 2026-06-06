<?php
declare(strict_types=1);

require __DIR__ . '/../../lib/bootstrap.php';
require __DIR__ . '/../../lib/session.php';
require_once __DIR__ . '/../../lib/flight-dispatch-selection.php';

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    json_response(['error' => 'METHOD_NOT_ALLOWED'], 405);
}

$session = require_auth_session();
$companyId = (int)$session['company_id'];
$payload = read_json_body();

$serviceId = (int)($payload['service_id'] ?? 0);
$selectedAircraftId = isset($payload['company_aircraft_id'])
    ? (int)$payload['company_aircraft_id']
    : (isset($payload['aircraft_id']) ? (int)$payload['aircraft_id'] : 0);

if ($serviceId <= 0) {
    json_response(['error' => 'INVALID_FLIGHT_ID'], 422);
}

$pdo = db();

try {
    $pdo->beginTransaction();

    $service = dispatch_fetch_flight_definition_for_update($pdo, $companyId, $serviceId);
    if (!$service) {
        $pdo->rollBack();
        json_response(['error' => 'FLIGHT_NOT_FOUND'], 404);
    }

    $isOnDemand = strtoupper((string)$service['service_type']) === 'ON_DEMAND';

    if ($isOnDemand && $selectedAircraftId <= 0) {
        $pdo->rollBack();
        json_response([
            'error' => 'AIRCRAFT_SELECTION_REQUIRED',
            'message' => 'Select an available aircraft at the origin airport before starting this non-scheduled flight.',
        ], 422);
    }

    $aircraft = $isOnDemand
        ? dispatch_fetch_specific_available_aircraft($pdo, $companyId, $service, $selectedAircraftId)
        : dispatch_choose_best_available_aircraft($pdo, $companyId, $service);

    if (!$aircraft) {
        $pdo->rollBack();
        json_response([
            'error' => 'NO_AVAILABLE_AIRCRAFT_AT_ORIGIN',
            'message' => 'No compatible available aircraft is present at the flight origin airport.',
            'origin_airport_icao_code' => $service['origin_airport_icao_code'],
            'compatible_aircraft_model_codes' => $service['compatible_aircraft_model_codes'] ?? '',
        ], 409);
    }

    $pilots = dispatch_fetch_pilots_for_aircraft_model($pdo, $companyId, (string)$aircraft['model_code']);
    if (count($pilots) < 2) {
        $pdo->rollBack();
        json_response([
            'error' => 'INSUFFICIENT_CREW',
            'message' => 'This aircraft cannot depart because there are not enough qualified active pilots.',
            'required_pilots' => 2,
            'available_pilots' => count($pilots),
            'aircraft_model_code' => $aircraft['model_code'],
            'icao_type_code' => $aircraft['icao_type_code'],
        ], 409);
    }

    $technician = dispatch_fetch_best_technician($pdo, $companyId);
    $flightCode = next_flight_instance_code($pdo, $companyId);
    $durationMinutes = max(20, (int)($service['estimated_block_minutes'] ?? 60));
    $now = gmdate('Y-m-d H:i:s');
    $arrival = gmdate('Y-m-d H:i:s', time() + ($durationMinutes * 60));

    $capacity = max(1, (int)($aircraft['passenger_capacity_standard'] ?? 1));
    $passengerCount = min($capacity, max(1, (int)floor($capacity * 0.75)));
    $ticketPrice = (float)($service['base_ticket_price'] ?? 0);
    $revenue = $passengerCount * $ticketPrice;
    $blockHours = $durationMinutes / 60.0;
    $fuelCost = $blockHours * (float)($aircraft['fuel_burn_kg_per_hour'] ?? 0) * 1.20;
    $maintenanceCost = $blockHours * (float)($aircraft['maintenance_cost_per_hour'] ?? 0);
    $staffCost = ((float)($pilots[0]['salary_per_flight'] ?? 0)) + ((float)($pilots[1]['salary_per_flight'] ?? 0));
    $operatingCost = $fuelCost + $maintenanceCost + $staffCost;
    $profit = $revenue - $operatingCost;

    $columns = table_columns($pdo, 'scheduled_flight_instances');
    $values = [];
    put($values, $columns, 'company_id', $companyId);
    put($values, $columns, 'scheduled_service_id', $serviceId);
    put($values, $columns, 'flight_code', $flightCode);
    put($values, $columns, 'flight_operation_type', $isOnDemand ? 'ON_DEMAND' : 'SCHEDULED');
    put($values, $columns, 'status', 'IN_FLIGHT');
    put($values, $columns, 'dispatch_status', $isOnDemand ? 'MANUAL_AIRCRAFT_SELECTED' : 'AUTO_SELECTED_PROFITABLE_AIRCRAFT');
    put($values, $columns, 'backup_used', 0);
    put($values, $columns, 'origin_airport_icao_code', $service['origin_airport_icao_code']);
    put($values, $columns, 'destination_airport_icao_code', $service['destination_airport_icao_code']);
    put($values, $columns, 'aircraft_id', (int)$aircraft['aircraft_id']);
    put($values, $columns, 'pilot_1_staff_id', (int)$pilots[0]['staff_id']);
    put($values, $columns, 'pilot_2_staff_id', (int)$pilots[1]['staff_id']);
    put($values, $columns, 'technician_staff_id', $technician ? (int)$technician['staff_id'] : null);
    put($values, $columns, 'passenger_count', $passengerCount);
    put($values, $columns, 'passenger_revenue', number_format($revenue, 2, '.', ''));
    put($values, $columns, 'fuel_cost', number_format($fuelCost, 2, '.', ''));
    put($values, $columns, 'maintenance_cost', number_format($maintenanceCost, 2, '.', ''));
    put($values, $columns, 'staff_cost', number_format($staffCost, 2, '.', ''));
    put($values, $columns, 'total_operating_cost', number_format($operatingCost, 2, '.', ''));
    put($values, $columns, 'profit_amount', number_format($profit, 2, '.', ''));
    put($values, $columns, 'currency_code', $service['currency_code'] ?? 'EUR');
    put($values, $columns, 'scheduled_departure_at_utc', $now);
    put($values, $columns, 'actual_departure_at_utc', $now);
    put($values, $columns, 'scheduled_arrival_at_utc', $arrival);
    put($values, $columns, 'actual_arrival_at_utc', null);

    $flightInstanceId = insert_dynamic($pdo, 'scheduled_flight_instances', $values);

    $pdo->prepare("
        UPDATE company_aircraft
        SET status = 'IN_FLIGHT',
            current_airport_icao_code = :destination
        WHERE id = :aircraft_id AND company_id = :company_id
    ")->execute([
        'destination' => $service['destination_airport_icao_code'],
        'aircraft_id' => (int)$aircraft['aircraft_id'],
        'company_id' => $companyId,
    ]);

    $pdo->commit();

    json_response([
        'status' => 'IN_FLIGHT',
        'flight_instance_id' => $flightInstanceId,
        'flight_code' => $flightCode,
        'dispatch_status' => $isOnDemand ? 'MANUAL_AIRCRAFT_SELECTED' : 'AUTO_SELECTED_PROFITABLE_AIRCRAFT',
        'aircraft' => [
            'company_aircraft_id' => (int)$aircraft['aircraft_id'],
            'registration_code' => $aircraft['registration_code'],
            'model_code' => $aircraft['model_code'],
            'icao_type_code' => $aircraft['icao_type_code'],
            'model_name' => $aircraft['model_name'],
        ],
        'crew' => [
            'pilot_1' => $pilots[0]['display_name'],
            'pilot_2' => $pilots[1]['display_name'],
            'technician' => $technician['display_name'] ?? null,
        ],
        'estimated_profit' => number_format($profit, 2, '.', ''),
        'scheduled_arrival_at_utc' => $arrival,
    ], 201);
} catch (Throwable $exception) {
    if ($pdo->inTransaction()) {
        $pdo->rollBack();
    }
    json_response(['error' => 'START_FLIGHT_FAILED', 'message' => $exception->getMessage()], 500);
}

function next_flight_instance_code(PDO $pdo, int $companyId): string
{
    $base = time();
    $candidate = 'IO-' . $base;
    $suffix = 0;
    $stmt = $pdo->prepare("
        SELECT COUNT(*)
        FROM scheduled_flight_instances
        WHERE company_id = :company_id AND flight_code = :flight_code
    ");
    while (true) {
        $code = $suffix === 0 ? $candidate : $candidate . '-' . $suffix;
        $stmt->execute(['company_id' => $companyId, 'flight_code' => $code]);
        if ((int)$stmt->fetchColumn() === 0) return $code;
        $suffix++;
    }
}

function table_columns(PDO $pdo, string $tableName): array
{
    $stmt = $pdo->prepare("
        SELECT COLUMN_NAME
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = :table_name
    ");
    $stmt->execute(['table_name' => $tableName]);
    return array_flip(array_map(static fn ($row) => $row['COLUMN_NAME'], $stmt->fetchAll()));
}

function put(array &$values, array $columns, string $column, mixed $value): void
{
    if (isset($columns[$column])) $values[$column] = $value;
}

function insert_dynamic(PDO $pdo, string $tableName, array $values): int
{
    $columns = array_keys($values);
    $quoted = array_map(static fn ($column) => "`{$column}`", $columns);
    $placeholders = array_map(static fn ($column) => ":{$column}", $columns);
    $sql = "INSERT INTO {$tableName} (" . implode(', ', $quoted) . ") VALUES (" . implode(', ', $placeholders) . ")";
    $stmt = $pdo->prepare($sql);
    foreach ($values as $column => $value) $stmt->bindValue(":{$column}", $value);
    $stmt->execute();
    return (int)$pdo->lastInsertId();
}
