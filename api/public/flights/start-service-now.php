<?php
declare(strict_types=1);

ini_set('display_errors', '1');
ini_set('display_startup_errors', '1');
error_reporting(E_ALL);

set_exception_handler(function (Throwable $exception): void {
    http_response_code(500);
    header('Content-Type: application/json; charset=utf-8');
    echo json_encode([
        'error' => 'UNCAUGHT_EXCEPTION',
        'message' => $exception->getMessage(),
        'file' => $exception->getFile(),
        'line' => $exception->getLine(),
    ], JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES);
    exit;
});

set_error_handler(function (int $severity, string $message, string $file, int $line): bool {
    throw new ErrorException($message, 0, $severity, $file, $line);
});

require __DIR__ . '/../../lib/bootstrap.php';
require __DIR__ . '/../../lib/session.php';
require_once __DIR__ . '/../../lib/dispatch-aircraft.php';

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    json_response(['error' => 'METHOD_NOT_ALLOWED'], 405);
}

$session = require_auth_session();
$companyId = (int)$session['company_id'];
$payload = read_json_body();
$serviceId = (int)($payload['service_id'] ?? $payload['route_id'] ?? 0);

if ($serviceId <= 0) {
    json_response(['error' => 'INVALID_SERVICE_ID'], 422);
}

$pdo = db();

try {
    $pdo->beginTransaction();

    $service = fetch_service($pdo, $companyId, $serviceId);
    if (!$service) {
        $pdo->rollBack();
        json_response(['error' => 'SERVICE_NOT_FOUND'], 404);
    }

    $aircraft = find_compatible_aircraft_for_flight($pdo, $companyId, (string)$service['origin_airport_icao_code'], [
        'required_aircraft_class' => $service['required_aircraft_class'] ?: 'LIGHT_COMMERCIAL',
        'preferred_aircraft_model_id' => $service['preferred_aircraft_model_id'],
        'min_range_km' => $service['planned_distance_km'] ?? 0,
        'min_passenger_capacity' => 1,
        'max_passenger_capacity' => 19,
    ]);

    if (!$aircraft) {
        $pdo->rollBack();
        json_response([
            'error' => 'NO_COMPATIBLE_AIRCRAFT_AT_ORIGIN',
            'message' => 'No compatible available aircraft was found at the service origin airport.',
            'origin_airport_icao_code' => $service['origin_airport_icao_code'],
            'required_aircraft_class' => $service['required_aircraft_class'],
        ], 409);
    }

    $pilots = fetch_c208_pilots($pdo, $companyId);
    if (count($pilots) < 2) {
        $pdo->rollBack();
        json_response([
            'error' => 'INSUFFICIENT_CREW',
            'message' => 'Two active CPL + C208_TYPE pilots are required to start this flight.',
            'current_qualified_pilots' => count($pilots),
            'required_qualified_pilots' => 2,
        ], 409);
    }

    $technician = fetch_c208_technician($pdo, $companyId);
    $columns = table_columns($pdo, 'scheduled_flight_instances');

    $flightCode = next_flight_code($pdo, $companyId);
    $now = gmdate('Y-m-d H:i:s');
    $date = gmdate('Y-m-d');
    $durationMinutes = max(20, (int)$service['estimated_block_minutes']);
    $arrival = gmdate('Y-m-d H:i:s', time() + $durationMinutes * 60);

    $capacity = (int)$aircraft['passenger_capacity_standard'];
    $ticket = (float)($service['base_ticket_price'] ?? 0);
    $passengers = max(1, min($capacity, (int)floor($capacity * 0.75)));
    $revenue = $passengers * $ticket;
    $blockHours = $durationMinutes / 60.0;
    $fuelCost = (float)($aircraft['fuel_burn_kg_per_hour'] ?? 170) * $blockHours * 1.15;
    $maintenanceCost = (float)($aircraft['maintenance_cost_per_hour'] ?? 350) * $blockHours;
    $crewCost = crew_cost($pilots, $revenue, $blockHours);
    $totalCost = $fuelCost + $maintenanceCost + $crewCost;
    $profit = $revenue - $totalCost;

    $v = [];
    put($v, $columns, 'company_id', $companyId);
    put($v, $columns, 'route_id', null);
    put($v, $columns, 'air_route_id', (int)$service['air_route_id']);
    put($v, $columns, 'scheduled_service_id', (int)$service['service_id']);
    put($v, $columns, 'flight_code', $flightCode);
    put($v, $columns, 'flight_operation_type', 'SCHEDULED');
    put($v, $columns, 'flight_date_utc', $date);
    put($v, $columns, 'aircraft_id', (int)$aircraft['aircraft_id']);
    put($v, $columns, 'planned_aircraft_id', (int)$aircraft['aircraft_id']);
    put($v, $columns, 'dispatch_aircraft_id', (int)$aircraft['aircraft_id']);
    put($v, $columns, 'dispatch_status', 'ASSIGNED');
    put($v, $columns, 'backup_used', 0);
    put($v, $columns, 'schedule_conflict_status', 'NONE');
    put($v, $columns, 'origin_airport_icao_code', $service['origin_airport_icao_code']);
    put($v, $columns, 'destination_airport_icao_code', $service['destination_airport_icao_code']);
    put($v, $columns, 'required_aircraft_class', $service['required_aircraft_class'] ?: 'LIGHT_COMMERCIAL');
    put($v, $columns, 'preferred_aircraft_model_id', $service['preferred_aircraft_model_id']);
    put($v, $columns, 'scheduled_departure_at_utc', $now);
    put($v, $columns, 'scheduled_arrival_at_utc', $arrival);
    put($v, $columns, 'actual_departure_at_utc', $now);
    put($v, $columns, 'actual_arrival_at_utc', null);
    put($v, $columns, 'planned_distance_km', $service['planned_distance_km']);
    put($v, $columns, 'planned_duration_minutes', $durationMinutes);
    put($v, $columns, 'status', 'IN_FLIGHT');
    put($v, $columns, 'assigned_pilot_1_id', (int)$pilots[0]['id']);
    put($v, $columns, 'assigned_pilot_2_id', (int)$pilots[1]['id']);
    put($v, $columns, 'pilot_1_id', (int)$pilots[0]['id']);
    put($v, $columns, 'pilot_2_id', (int)$pilots[1]['id']);
    if ($technician) {
        put($v, $columns, 'assigned_technician_id', (int)$technician['id']);
        put($v, $columns, 'technician_id', (int)$technician['id']);
    }
    put($v, $columns, 'passenger_capacity', $capacity);
    put($v, $columns, 'passenger_count', $passengers);
    put($v, $columns, 'load_factor_percent', round(($passengers / max(1, $capacity)) * 100, 2));
    put($v, $columns, 'ticket_price', money($ticket));
    put($v, $columns, 'passenger_revenue', money($revenue));
    put($v, $columns, 'fuel_cost', money($fuelCost));
    put($v, $columns, 'maintenance_cost', money($maintenanceCost));
    put($v, $columns, 'crew_cost', money($crewCost));
    put($v, $columns, 'total_operating_cost', money($totalCost));
    put($v, $columns, 'profit_amount', money($profit));
    put($v, $columns, 'currency_code', $service['currency_code'] ?? 'EUR');

    $flightId = insert_dynamic($pdo, 'scheduled_flight_instances', $v);

    $pdo->prepare("UPDATE company_aircraft SET status = 'IN_FLIGHT' WHERE id = :aircraft_id AND company_id = :company_id")
        ->execute(['aircraft_id' => (int)$aircraft['aircraft_id'], 'company_id' => $companyId]);

    $pdo->commit();

    json_response([
        'status' => 'IN_FLIGHT',
        'flight_id' => $flightId,
        'flight_code' => $flightCode,
        'service_code' => $service['service_code'],
        'route_code' => $service['route_code'],
        'aircraft' => [
            'id' => (int)$aircraft['aircraft_id'],
            'registration_code' => $aircraft['registration_code'],
            'model_name' => $aircraft['model_name'],
        ],
        'crew' => [
            'pilot_1' => $pilots[0]['display_name'],
            'pilot_2' => $pilots[1]['display_name'],
            'technician' => $technician['display_name'] ?? null,
        ],
        'scheduled_arrival_at_utc' => $arrival,
        'passenger_count' => $passengers,
        'passenger_revenue' => money($revenue),
        'estimated_profit' => money($profit),
    ]);
} catch (Throwable $e) {
    if ($pdo->inTransaction()) $pdo->rollBack();
    json_response(['error' => 'START_SERVICE_FLIGHT_FAILED', 'message' => $e->getMessage()], 500);
}

function fetch_service(PDO $pdo, int $companyId, int $serviceId): ?array {
    $stmt = $pdo->prepare("
        SELECT ss.id AS service_id, ss.company_id, ss.air_route_id, ss.service_code,
               ss.preferred_aircraft_model_id, ss.required_aircraft_class,
               ss.base_ticket_price, ss.currency_code,
               ar.route_code, ar.origin_airport_icao_code, ar.destination_airport_icao_code,
               ar.planned_distance_km, ar.estimated_block_minutes
        FROM scheduled_services ss
        JOIN air_routes ar ON ar.id = ss.air_route_id
        WHERE ss.company_id = :company_id AND ss.id = :service_id AND ss.service_status = 'ACTIVE'
        LIMIT 1
    ");
    $stmt->execute(['company_id' => $companyId, 'service_id' => $serviceId]);
    $row = $stmt->fetch();
    return $row ?: null;
}

function fetch_c208_pilots(PDO $pdo, int $companyId): array {
    $hourly = column_exists($pdo, 'company_staff', 'hourly_rate') ? "s.hourly_rate" : "0.00 AS hourly_rate";
    $stmt = $pdo->prepare("
        SELECT s.id, s.display_name, s.salary_per_flight, {$hourly}, s.revenue_share_percent
        FROM company_staff s
        WHERE s.company_id = :company_id AND s.staff_role = 'PILOT' AND s.employment_status = 'ACTIVE'
          AND EXISTS (SELECT 1 FROM company_staff_licenses l WHERE l.company_staff_id = s.id AND l.license_code = 'CPL')
          AND EXISTS (SELECT 1 FROM company_staff_licenses l WHERE l.company_staff_id = s.id AND l.license_code = 'C208_TYPE')
        ORDER BY s.reliability_score DESC, s.fatigue_score ASC, s.id
        LIMIT 2
    ");
    $stmt->execute(['company_id' => $companyId]);
    return $stmt->fetchAll();
}

function fetch_c208_technician(PDO $pdo, int $companyId): ?array {
    $stmt = $pdo->prepare("
        SELECT s.id, s.display_name
        FROM company_staff s
        WHERE s.company_id = :company_id AND s.staff_role = 'TECHNICIAN' AND s.employment_status = 'ACTIVE'
          AND EXISTS (SELECT 1 FROM company_staff_licenses l WHERE l.company_staff_id = s.id AND l.license_code = 'C208_MAINT')
        ORDER BY s.reliability_score DESC, s.id
        LIMIT 1
    ");
    $stmt->execute(['company_id' => $companyId]);
    $row = $stmt->fetch();
    return $row ?: null;
}

function crew_cost(array $pilots, float $revenue, float $blockHours): float {
    $cost = 0.0;
    foreach ($pilots as $p) {
        $cost += (float)$p['salary_per_flight'];
        $cost += (float)$p['hourly_rate'] * $blockHours;
        $cost += $revenue * ((float)$p['revenue_share_percent'] / 100.0);
    }
    return $cost;
}

function table_columns(PDO $pdo, string $tableName): array {
    $stmt = $pdo->prepare("SELECT COLUMN_NAME FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = :table_name");
    $stmt->execute(['table_name' => $tableName]);
    return array_flip(array_map(static fn($r) => $r['COLUMN_NAME'], $stmt->fetchAll()));
}
function column_exists(PDO $pdo, string $tableName, string $columnName): bool {
    $stmt = $pdo->prepare("SELECT COUNT(*) FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = :table_name AND COLUMN_NAME = :column_name");
    $stmt->execute(['table_name' => $tableName, 'column_name' => $columnName]);
    return (int)$stmt->fetchColumn() > 0;
}
function put(array &$values, array $columns, string $column, mixed $value): void {
    if (isset($columns[$column])) $values[$column] = $value;
}
function insert_dynamic(PDO $pdo, string $tableName, array $values): int {
    $cols = array_keys($values);
    $quoted = array_map(static fn($c) => "`{$c}`", $cols);
    $ph = array_map(static fn($c) => ":{$c}", $cols);
    $stmt = $pdo->prepare("INSERT INTO {$tableName} (" . implode(', ', $quoted) . ") VALUES (" . implode(', ', $ph) . ")");
    foreach ($values as $c => $v) $stmt->bindValue(":{$c}", $v);
    $stmt->execute();
    return (int)$pdo->lastInsertId();
}
function next_flight_code(PDO $pdo, int $companyId): string {
    $base = time();
    $code = 'IO-' . $base;

    $stmt = $pdo->prepare("
        SELECT COUNT(*)
        FROM scheduled_flight_instances
        WHERE company_id = :company_id
          AND flight_code = :flight_code
    ");

    $suffix = 0;

    while (true) {
        $candidate = $suffix === 0 ? $code : $code . '-' . $suffix;
        $stmt->execute([
            'company_id' => $companyId,
            'flight_code' => $candidate,
        ]);

        if ((int)$stmt->fetchColumn() === 0) {
            return $candidate;
        }

        $suffix++;
    }
}
function money(float $v): string { return number_format($v, 2, '.', ''); }
