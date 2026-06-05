<?php
declare(strict_types=1);

require __DIR__ . '/../../lib/bootstrap.php';
require __DIR__ . '/../../lib/session.php';
require __DIR__ . '/../../lib/flight-completion.php';

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    json_response(['error' => 'METHOD_NOT_ALLOWED'], 405);
}

$session = require_auth_session();
$companyId = $session['company_id'];

$payload = read_json_body();
$routeId = (int)($payload['route_id'] ?? 0);
$forceNow = (bool)($payload['force_now'] ?? true);

if ($routeId <= 0) {
    json_response(['error' => 'VALIDATION_ERROR', 'message' => 'route_id is required.'], 422);
}

$pdo = db();

try {
    $pdo->beginTransaction();

    complete_due_flights($pdo, $companyId);

    $routeStmt = $pdo->prepare("
        SELECT *
        FROM v_company_routes
        WHERE route_id = :route_id
          AND company_id = :company_id
          AND status = 'ACTIVE'
        LIMIT 1
    ");
    $routeStmt->execute([
        'route_id' => $routeId,
        'company_id' => $companyId,
    ]);
    $route = $routeStmt->fetch();

    if (!$route) {
        $pdo->rollBack();
        json_response(['error' => 'ROUTE_NOT_FOUND'], 404);
    }

    $crew = validate_dispatch_pilots($pdo, $companyId, $route);

    if (!$crew['ok']) {
        $pdo->rollBack();
        json_response([
            'error' => $crew['error'],
            'message' => $crew['message'],
            'future_mailbox_event' => [
                'type' => 'CREW_BLOCKED',
                'options' => ['ASSIGN_PILOTS', 'DELAY_FLIGHT', 'CANCEL_FLIGHT']
            ],
        ], 409);
    }

    $aircraft = find_dispatch_aircraft($pdo, $companyId, $route);

    if (!$aircraft) {
        $pdo->rollBack();
        json_response([
            'error' => 'NO_AVAILABLE_AIRCRAFT_AT_ORIGIN',
            'message' => 'No available Cessna 208B is currently at the route origin airport. The route remains valid, but this flight cannot depart now.',
            'future_mailbox_event' => [
                'type' => 'DISPATCH_BLOCKED',
                'options' => ['SUBSTITUTE_AIRCRAFT', 'DELAY_FLIGHT', 'CANCEL_FLIGHT']
            ],
        ], 409);
    }

    if ((float)$aircraft['condition_percent'] <= 45.0 || $aircraft['status'] === 'MAINTENANCE') {
        $pdo->rollBack();
        json_response([
            'error' => 'AIRCRAFT_MAINTENANCE_REQUIRED',
            'message' => 'Aircraft is not fit for dispatch. Maintenance must be planned before departure.',
            'future_mailbox_event' => [
                'type' => 'MAINTENANCE_REQUIRED',
                'options' => ['SCHEDULE_MAINTENANCE', 'SUBSTITUTE_AIRCRAFT', 'DELAY_FLIGHT', 'CANCEL_FLIGHT']
            ],
        ], 409);
    }

    $flightDate = gmdate('Y-m-d');
    $scheduledDeparture = $flightDate . ' ' . $route['scheduled_departure_time_utc'];
    $actualDeparture = $forceNow ? gmdate('Y-m-d H:i:s') : $scheduledDeparture;

    $arrivalTs = strtotime($actualDeparture . ' UTC') + ((int)$route['planned_duration_minutes'] * 60);
    $scheduledArrival = gmdate('Y-m-d H:i:s', $arrivalTs);

    $capacity = (int)$aircraft['passenger_capacity_standard'];
    $loadFactor = random_int(55, 100);
    $passengers = max(1, min($capacity, (int)floor($capacity * $loadFactor / 100)));

    $ticketPrice = (float)$route['ticket_price'];
    $revenue = $passengers * $ticketPrice;

    $durationHours = ((int)$route['planned_duration_minutes']) / 60.0;
    $fuelPricePerKg = 1.15;
    $fuelCost = ((float)$aircraft['fuel_burn_kg_per_hour']) * $durationHours * $fuelPricePerKg;
    $maintenanceCost = ((float)$aircraft['maintenance_cost_per_hour']) * $durationHours;
    $staffCost = calculate_pilot_cost($pdo, $companyId, $route, $revenue);

    $totalCost = $fuelCost + $maintenanceCost + $staffCost;
    $profit = $revenue - $totalCost;

    $flightCode = 'IO' . str_pad((string)$routeId, 3, '0', STR_PAD_LEFT) . '-' . str_replace('-', '', $flightDate);

    $insert = $pdo->prepare("
        INSERT INTO scheduled_flight_instances (
          route_id,
          company_id,
          aircraft_id,
          flight_code,
          flight_date_utc,
          origin_airport_icao_code,
          destination_airport_icao_code,
          scheduled_departure_at_utc,
          scheduled_arrival_at_utc,
          actual_departure_at_utc,
          status,
          passenger_capacity,
          passenger_count,
          load_factor_percent,
          ticket_price,
          passenger_revenue,
          fuel_cost,
          maintenance_cost,
          staff_cost,
          total_operating_cost,
          profit_amount,
          currency_code
        ) VALUES (
          :route_id,
          :company_id,
          :aircraft_id,
          :flight_code,
          :flight_date_utc,
          :origin,
          :destination,
          :scheduled_departure,
          :scheduled_arrival,
          :actual_departure,
          'IN_FLIGHT',
          :capacity,
          :passengers,
          :load_factor,
          :ticket_price,
          :revenue,
          :fuel_cost,
          :maintenance_cost,
          :staff_cost,
          :total_cost,
          :profit,
          :currency_code
        )
        ON DUPLICATE KEY UPDATE
          status = IF(status = 'COMPLETED', status, VALUES(status)),
          actual_departure_at_utc = IF(status = 'COMPLETED', actual_departure_at_utc, VALUES(actual_departure_at_utc)),
          scheduled_arrival_at_utc = IF(status = 'COMPLETED', scheduled_arrival_at_utc, VALUES(scheduled_arrival_at_utc))
    ");

    $insert->execute([
        'route_id' => $routeId,
        'company_id' => $companyId,
        'aircraft_id' => (int)$aircraft['id'],
        'flight_code' => $flightCode,
        'flight_date_utc' => $flightDate,
        'origin' => $route['origin_airport_icao_code'],
        'destination' => $route['destination_airport_icao_code'],
        'scheduled_departure' => $scheduledDeparture,
        'scheduled_arrival' => $scheduledArrival,
        'actual_departure' => $actualDeparture,
        'capacity' => $capacity,
        'passengers' => $passengers,
        'load_factor' => $loadFactor,
        'ticket_price' => $ticketPrice,
        'revenue' => number_format($revenue, 2, '.', ''),
        'fuel_cost' => number_format($fuelCost, 2, '.', ''),
        'maintenance_cost' => number_format($maintenanceCost, 2, '.', ''),
        'staff_cost' => number_format($staffCost, 2, '.', ''),
        'total_cost' => number_format($totalCost, 2, '.', ''),
        'profit' => number_format($profit, 2, '.', ''),
        'currency_code' => $route['currency_code'],
    ]);

    $flightId = (int)$pdo->lastInsertId();

    $updateAircraft = $pdo->prepare("
        UPDATE company_aircraft
        SET status = 'IN_FLIGHT'
        WHERE id = :aircraft_id
          AND company_id = :company_id
    ");
    $updateAircraft->execute([
        'aircraft_id' => (int)$aircraft['id'],
        'company_id' => $companyId,
    ]);

    if (empty($route['aircraft_id'])) {
        $pdo->prepare("
            UPDATE company_routes
            SET aircraft_id = :aircraft_id
            WHERE id = :route_id
              AND company_id = :company_id
        ")->execute([
            'aircraft_id' => (int)$aircraft['id'],
            'route_id' => $routeId,
            'company_id' => $companyId,
        ]);
    }

    $pdo->commit();

    json_response([
        'flight_instance_id' => $flightId,
        'flight_code' => $flightCode,
        'status' => 'IN_FLIGHT',
        'passenger_count' => $passengers,
        'passenger_capacity' => $capacity,
        'passenger_revenue' => number_format($revenue, 2, '.', ''),
        'total_operating_cost' => number_format($totalCost, 2, '.', ''),
        'profit_amount' => number_format($profit, 2, '.', ''),
        'scheduled_arrival_at_utc' => $scheduledArrival,
    ], 201);
} catch (Throwable $exception) {
    if ($pdo->inTransaction()) {
        $pdo->rollBack();
    }

    json_response([
        'error' => 'DATABASE_ERROR',
        'message' => 'Unable to start scheduled flight.',
    ], 500);
}

function find_dispatch_aircraft(PDO $pdo, int $companyId, array $route): ?array
{
    $baseSql = "
        SELECT
          ca.id,
          ca.registration_code,
          ca.status,
          ca.current_airport_icao_code,
          ca.condition_percent,
          am.model_code,
          am.passenger_capacity_standard,
          am.cruise_speed_kmh,
          am.range_km,
          am.fuel_burn_kg_per_hour,
          am.maintenance_cost_per_hour
        FROM company_aircraft ca
        JOIN aircraft_models am
          ON am.id = ca.aircraft_model_id
        WHERE ca.company_id = :company_id
          AND ca.status IN ('AVAILABLE', 'PARKED')
          AND ca.current_airport_icao_code = :origin
          AND am.model_code = 'C208B_GRAND_CARAVAN_EX'
    ";

    if (!empty($route['aircraft_id'])) {
        $stmt = $pdo->prepare($baseSql . " AND ca.id = :aircraft_id LIMIT 1 FOR UPDATE");
        $stmt->execute([
            'company_id' => $companyId,
            'origin' => $route['origin_airport_icao_code'],
            'aircraft_id' => (int)$route['aircraft_id'],
        ]);
        $row = $stmt->fetch();

        if ($row) {
            return $row;
        }
    }

    $stmt = $pdo->prepare($baseSql . " ORDER BY ca.id LIMIT 1 FOR UPDATE");
    $stmt->execute([
        'company_id' => $companyId,
        'origin' => $route['origin_airport_icao_code'],
    ]);
    $row = $stmt->fetch();

    return $row ?: null;
}

function validate_dispatch_pilots(PDO $pdo, int $companyId, array $route): array
{
    if (empty($route['assigned_pilot_1_id']) || empty($route['assigned_pilot_2_id'])) {
        return [
            'ok' => false,
            'error' => 'MISSING_PILOTS',
            'message' => 'Two active pilots with CPL and C208_TYPE are required.',
        ];
    }

    $stmt = $pdo->prepare("
        SELECT COUNT(*)
        FROM company_staff s
        WHERE s.company_id = :company_id
          AND s.id IN (:p1, :p2)
          AND s.staff_role = 'PILOT'
          AND s.employment_status = 'ACTIVE'
          AND EXISTS (
            SELECT 1
            FROM company_staff_licenses l
            WHERE l.company_staff_id = s.id
              AND l.license_code = 'CPL'
          )
          AND EXISTS (
            SELECT 1
            FROM company_staff_licenses l
            WHERE l.company_staff_id = s.id
              AND l.license_code = 'C208_TYPE'
          )
    ");
    $stmt->execute([
        'company_id' => $companyId,
        'p1' => (int)$route['assigned_pilot_1_id'],
        'p2' => (int)$route['assigned_pilot_2_id'],
    ]);

    if ((int)$stmt->fetchColumn() < 2) {
        return [
            'ok' => false,
            'error' => 'PILOTS_NOT_QUALIFIED',
            'message' => 'Assigned pilots are not both active and qualified for Cessna passenger operations.',
        ];
    }

    return ['ok' => true];
}

function calculate_pilot_cost(PDO $pdo, int $companyId, array $route, float $revenue): float
{
    $stmt = $pdo->prepare("
        SELECT
          SUM(salary_per_flight) AS pilot_salary,
          SUM(revenue_share_percent) AS pilot_revenue_share
        FROM company_staff
        WHERE company_id = :company_id
          AND id IN (:p1, :p2)
    ");
    $stmt->execute([
        'company_id' => $companyId,
        'p1' => (int)$route['assigned_pilot_1_id'],
        'p2' => (int)$route['assigned_pilot_2_id'],
    ]);

    $staff = $stmt->fetch();

    $pilotSalary = (float)($staff['pilot_salary'] ?? 0);
    $pilotRevenueSharePercent = (float)($staff['pilot_revenue_share'] ?? 0);

    return $pilotSalary + ($revenue * $pilotRevenueSharePercent / 100.0);
}
