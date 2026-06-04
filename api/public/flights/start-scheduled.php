<?php
declare(strict_types=1);

require __DIR__ . '/../../lib/bootstrap.php';
require __DIR__ . '/../../lib/session.php';

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

    $aircraftStmt = $pdo->prepare("
        SELECT ca.status
        FROM company_aircraft ca
        WHERE ca.id = :aircraft_id
          AND ca.company_id = :company_id
        LIMIT 1
        FOR UPDATE
    ");
    $aircraftStmt->execute([
        'aircraft_id' => (int)$route['aircraft_id'],
        'company_id' => $companyId,
    ]);
    $aircraftStatus = $aircraftStmt->fetchColumn();

    if (!in_array($aircraftStatus, ['AVAILABLE', 'PARKED'], true)) {
        $pdo->rollBack();
        json_response(['error' => 'AIRCRAFT_NOT_AVAILABLE'], 409);
    }

    $flightDate = gmdate('Y-m-d');
    $scheduledDeparture = $flightDate . ' ' . $route['scheduled_departure_time_utc'];
    $actualDeparture = $forceNow ? gmdate('Y-m-d H:i:s') : $scheduledDeparture;

    $arrivalTs = strtotime($actualDeparture . ' UTC') + ((int)$route['planned_duration_minutes'] * 60);
    $scheduledArrival = gmdate('Y-m-d H:i:s', $arrivalTs);

    $capacity = (int)$route['passenger_capacity_standard'];
    $loadFactor = random_int(55, 100);
    $passengers = max(1, min($capacity, (int)floor($capacity * $loadFactor / 100)));

    $ticketPrice = (float)$route['ticket_price'];
    $revenue = $passengers * $ticketPrice;

    $durationHours = ((int)$route['planned_duration_minutes']) / 60.0;
    $fuelPricePerKg = 1.15;
    $fuelCost = ((float)$route['fuel_burn_kg_per_hour']) * $durationHours * $fuelPricePerKg;
    $maintenanceCost = ((float)$route['maintenance_cost_per_hour']) * $durationHours;

    $staffStmt = $pdo->prepare("
        SELECT
          SUM(CASE WHEN id IN (:p1, :p2) THEN salary_per_flight ELSE 0 END) AS pilot_salary,
          SUM(CASE WHEN id IN (:p1b, :p2b) THEN revenue_share_percent ELSE 0 END) AS pilot_revenue_share,
          SUM(CASE WHEN id = :tech THEN daily_retainer ELSE 0 END) AS technician_cost
        FROM company_staff
        WHERE company_id = :company_id
          AND id IN (:p1c, :p2c, :techc)
    ");
    $staffStmt->execute([
        'p1' => (int)$route['assigned_pilot_1_id'] ?? 0,
        'p2' => (int)$route['assigned_pilot_2_id'] ?? 0,
        'p1b' => (int)$route['assigned_pilot_1_id'] ?? 0,
        'p2b' => (int)$route['assigned_pilot_2_id'] ?? 0,
        'tech' => (int)$route['assigned_technician_id'] ?? 0,
        'company_id' => $companyId,
        'p1c' => (int)$route['assigned_pilot_1_id'] ?? 0,
        'p2c' => (int)$route['assigned_pilot_2_id'] ?? 0,
        'techc' => (int)$route['assigned_technician_id'] ?? 0,
    ]);
    $staff = $staffStmt->fetch();

    $pilotSalary = (float)($staff['pilot_salary'] ?? 0);
    $pilotRevenueSharePercent = (float)($staff['pilot_revenue_share'] ?? 0);
    $technicianCost = (float)($staff['technician_cost'] ?? 0);
    $staffCost = $pilotSalary + $technicianCost + ($revenue * $pilotRevenueSharePercent / 100.0);

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
        'aircraft_id' => (int)$route['aircraft_id'],
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
        'aircraft_id' => (int)$route['aircraft_id'],
        'company_id' => $companyId,
    ]);

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

function complete_due_flights(PDO $pdo, int $companyId): void
{
    $stmt = $pdo->prepare("
        SELECT id, aircraft_id, destination_airport_icao_code, profit_amount
        FROM scheduled_flight_instances
        WHERE company_id = :company_id
          AND status = 'IN_FLIGHT'
          AND scheduled_arrival_at_utc <= UTC_TIMESTAMP()
        FOR UPDATE
    ");
    $stmt->execute(['company_id' => $companyId]);
    $flights = $stmt->fetchAll();

    foreach ($flights as $flight) {
        $pdo->prepare("
            UPDATE scheduled_flight_instances
            SET
              status = 'COMPLETED',
              actual_arrival_at_utc = UTC_TIMESTAMP()
            WHERE id = :id
        ")->execute(['id' => (int)$flight['id']]);

        $pdo->prepare("
            UPDATE company_aircraft
            SET
              status = 'AVAILABLE',
              current_airport_icao_code = :destination
            WHERE id = :aircraft_id
              AND company_id = :company_id
        ")->execute([
            'destination' => $flight['destination_airport_icao_code'],
            'aircraft_id' => (int)$flight['aircraft_id'],
            'company_id' => $companyId,
        ]);

        $pdo->prepare("
            UPDATE companies
            SET budget_amount = budget_amount + :profit
            WHERE id = :company_id
        ")->execute([
            'profit' => (float)$flight['profit_amount'],
            'company_id' => $companyId,
        ]);
    }
}
