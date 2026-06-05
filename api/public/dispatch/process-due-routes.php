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

$windowMinutes = max(1, min(240, (int)($payload['window_minutes'] ?? 60)));
$devForce = (bool)($payload['dev_force_due'] ?? false);

$pdo = db();

try {
    $pdo->beginTransaction();

    complete_due_flights($pdo, $companyId);

    $routesStmt = $pdo->prepare("
        SELECT *
        FROM v_company_routes
        WHERE company_id = :company_id
          AND status = 'ACTIVE'
          AND auto_dispatch_enabled = TRUE
        ORDER BY scheduled_departure_time_utc, route_id
    ");
    $routesStmt->execute(['company_id' => $companyId]);
    $routes = $routesStmt->fetchAll();

    $results = [];

    foreach ($routes as $route) {
        $scheduledDeparture = gmdate('Y-m-d') . ' ' . $route['scheduled_departure_time_utc'];

        if (!$devForce && strtotime($scheduledDeparture . ' UTC') > time() + ($windowMinutes * 60)) {
            continue;
        }

        if (already_processed_today($pdo, (int)$route['route_id'], $scheduledDeparture)) {
            $results[] = [
                'route_id' => (int)$route['route_id'],
                'result' => 'SKIPPED_ALREADY_PROCESSED',
            ];
            continue;
        }

        $crew = validate_dispatch_pilots($pdo, $companyId, $route);
        if (!$crew['ok']) {
            $results[] = record_blocked_dispatch($pdo, $companyId, $route, $scheduledDeparture, 'BLOCKED_CREW', $crew['message'], -4, -250.00);
            continue;
        }

        $selected = find_aircraft_for_dispatch($pdo, $companyId, $route);

        if (!$selected) {
            $results[] = record_blocked_dispatch(
                $pdo,
                $companyId,
                $route,
                $scheduledDeparture,
                'CANCELLED_NO_AIRCRAFT',
                'No available compatible aircraft at origin. Passengers are sent home or rebooked.',
                -8,
                -600.00
            );
            continue;
        }

        $flight = start_flight_from_route($pdo, $companyId, $route, $selected, $scheduledDeparture);
        $results[] = [
            'route_id' => (int)$route['route_id'],
            'result' => $selected['role'] === 'BACKUP' ? 'STARTED_BACKUP' : 'STARTED_PRIMARY',
            'aircraft_id' => (int)$selected['id'],
            'registration_code' => $selected['registration_code'],
            'flight_code' => $flight['flight_code'],
        ];
    }

    $pdo->commit();

    json_response([
        'processed_count' => count($results),
        'results' => $results,
    ]);
} catch (Throwable $exception) {
    if ($pdo->inTransaction()) {
        $pdo->rollBack();
    }

    json_response([
        'error' => 'DATABASE_ERROR',
        'message' => 'Unable to process dispatch.',
    ], 500);
}

function already_processed_today(PDO $pdo, int $routeId, string $scheduledDeparture): bool
{
    $stmt = $pdo->prepare("
        SELECT COUNT(*)
        FROM route_dispatch_attempts
        WHERE route_id = :route_id
          AND scheduled_departure_at_utc = :scheduled_departure
    ");
    $stmt->execute([
        'route_id' => $routeId,
        'scheduled_departure' => $scheduledDeparture,
    ]);

    if ((int)$stmt->fetchColumn() > 0) {
        return true;
    }

    $stmt = $pdo->prepare("
        SELECT COUNT(*)
        FROM scheduled_flight_instances
        WHERE route_id = :route_id
          AND scheduled_departure_at_utc = :scheduled_departure
    ");
    $stmt->execute([
        'route_id' => $routeId,
        'scheduled_departure' => $scheduledDeparture,
    ]);

    return (int)$stmt->fetchColumn() > 0;
}

function validate_dispatch_pilots(PDO $pdo, int $companyId, array $route): array
{
    if (empty($route['assigned_pilot_1_id']) || empty($route['assigned_pilot_2_id'])) {
        return ['ok' => false, 'message' => 'Two pilots are not assigned to this route.'];
    }

    $stmt = $pdo->prepare("
        SELECT COUNT(*)
        FROM company_staff s
        WHERE s.company_id = :company_id
          AND s.id IN (:p1, :p2)
          AND s.staff_role = 'PILOT'
          AND s.employment_status = 'ACTIVE'
          AND EXISTS (
            SELECT 1 FROM company_staff_licenses l
            WHERE l.company_staff_id = s.id
              AND l.license_code = 'CPL'
          )
          AND EXISTS (
            SELECT 1 FROM company_staff_licenses l
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
        return ['ok' => false, 'message' => 'Assigned pilots are not both active and C208 qualified.'];
    }

    return ['ok' => true];
}

function find_aircraft_for_dispatch(PDO $pdo, int $companyId, array $route): ?array
{
    if (!empty($route['aircraft_id'])) {
        $stmt = $pdo->prepare("
            SELECT
              ca.id,
              ca.registration_code,
              ca.status,
              ca.current_airport_icao_code,
              ca.condition_percent,
              am.model_code,
              am.passenger_capacity_standard,
              am.fuel_burn_kg_per_hour,
              am.maintenance_cost_per_hour,
              'PRIMARY' AS role
            FROM company_aircraft ca
            JOIN aircraft_models am ON am.id = ca.aircraft_model_id
            WHERE ca.id = :aircraft_id
              AND ca.company_id = :company_id
              AND ca.current_airport_icao_code = :origin
              AND ca.status IN ('AVAILABLE', 'PARKED')
              AND ca.condition_percent > 45.00
            LIMIT 1
            FOR UPDATE
        ");
        $stmt->execute([
            'aircraft_id' => (int)$route['aircraft_id'],
            'company_id' => $companyId,
            'origin' => $route['origin_airport_icao_code'],
        ]);
        $row = $stmt->fetch();

        if ($row) {
            return $row;
        }
    }

    if (!(bool)$route['allow_backup_aircraft']) {
        return null;
    }

    $stmt = $pdo->prepare("
        SELECT
          ca.id,
          ca.registration_code,
          ca.status,
          ca.current_airport_icao_code,
          ca.condition_percent,
          am.model_code,
          am.passenger_capacity_standard,
          am.fuel_burn_kg_per_hour,
          am.maintenance_cost_per_hour,
          'BACKUP' AS role
        FROM company_aircraft ca
        JOIN aircraft_models am ON am.id = ca.aircraft_model_id
        WHERE ca.company_id = :company_id
          AND ca.current_airport_icao_code = :origin
          AND ca.status IN ('AVAILABLE', 'PARKED')
          AND ca.condition_percent > 45.00
          AND am.model_code = 'C208B_GRAND_CARAVAN_EX'
        ORDER BY ca.id
        LIMIT 1
        FOR UPDATE
    ");
    $stmt->execute([
        'company_id' => $companyId,
        'origin' => $route['origin_airport_icao_code'],
    ]);

    $row = $stmt->fetch();
    return $row ?: null;
}

function start_flight_from_route(PDO $pdo, int $companyId, array $route, array $aircraft, string $scheduledDeparture): array
{
    $actualDeparture = gmdate('Y-m-d H:i:s');
    $arrivalTs = strtotime($actualDeparture . ' UTC') + ((int)$route['planned_duration_minutes'] * 60);
    $scheduledArrival = gmdate('Y-m-d H:i:s', $arrivalTs);

    $capacity = (int)$aircraft['passenger_capacity_standard'];
    $loadFactor = random_int(55, 100);
    $passengers = max(1, min($capacity, (int)floor($capacity * $loadFactor / 100)));
    $ticketPrice = (float)$route['ticket_price'];
    $revenue = $passengers * $ticketPrice;

    $durationHours = ((int)$route['planned_duration_minutes']) / 60.0;
    $fuelCost = ((float)$aircraft['fuel_burn_kg_per_hour']) * $durationHours * 1.15;
    $maintenanceCost = ((float)$aircraft['maintenance_cost_per_hour']) * $durationHours;
    $staffCost = calculate_pilot_cost($pdo, $companyId, $route, $revenue);
    $totalCost = $fuelCost + $maintenanceCost + $staffCost;
    $profit = $revenue - $totalCost;

    $flightDate = substr($scheduledDeparture, 0, 10);
    $flightCode = 'IO' . str_pad((string)$route['route_id'], 3, '0', STR_PAD_LEFT) . '-' . str_replace('-', '', $flightDate);

    $stmt = $pdo->prepare("
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
    ");
    $stmt->execute([
        'route_id' => (int)$route['route_id'],
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

    $pdo->prepare("
        UPDATE company_aircraft
        SET status = 'IN_FLIGHT'
        WHERE id = :aircraft_id
          AND company_id = :company_id
    ")->execute([
        'aircraft_id' => (int)$aircraft['id'],
        'company_id' => $companyId,
    ]);

    $result = $aircraft['role'] === 'BACKUP' ? 'STARTED_BACKUP' : 'STARTED_PRIMARY';

    $pdo->prepare("
        INSERT INTO route_dispatch_attempts (
          route_id,
          company_id,
          scheduled_departure_at_utc,
          result,
          reason,
          selected_aircraft_id,
          selected_aircraft_role,
          reputation_delta,
          budget_delta,
          currency_code
        ) VALUES (
          :route_id,
          :company_id,
          :scheduled_departure,
          :result,
          :reason,
          :aircraft_id,
          :aircraft_role,
          0,
          0.00,
          :currency_code
        )
    ")->execute([
        'route_id' => (int)$route['route_id'],
        'company_id' => $companyId,
        'scheduled_departure' => $scheduledDeparture,
        'result' => $result,
        'reason' => $aircraft['role'] === 'BACKUP' ? 'Backup aircraft used because primary was not available at origin.' : 'Primary aircraft dispatched.',
        'aircraft_id' => (int)$aircraft['id'],
        'aircraft_role' => $aircraft['role'],
        'currency_code' => $route['currency_code'],
    ]);

    $pdo->prepare("
        UPDATE company_routes
        SET
          last_dispatch_attempt_at_utc = UTC_TIMESTAMP(),
          last_dispatch_result = :result
        WHERE id = :route_id
          AND company_id = :company_id
    ")->execute([
        'result' => $result,
        'route_id' => (int)$route['route_id'],
        'company_id' => $companyId,
    ]);

    return ['flight_code' => $flightCode];
}

function record_blocked_dispatch(PDO $pdo, int $companyId, array $route, string $scheduledDeparture, string $result, string $reason, int $reputationDelta, float $budgetDelta): array
{
    $title = 'Scheduled flight could not depart';
    $body = sprintf(
        'Route %s → %s scheduled at %s could not depart. Reason: %s',
        $route['origin_airport_icao_code'],
        $route['destination_airport_icao_code'],
        $scheduledDeparture,
        $reason
    );

    $mail = $pdo->prepare("
        INSERT INTO game_mailbox_messages (
          company_id,
          message_type,
          severity,
          status,
          title,
          body,
          related_entity_type,
          related_entity_id,
          action_payload_json
        ) VALUES (
          :company_id,
          'DISPATCH_BLOCKED',
          'WARNING',
          'UNREAD',
          :title,
          :body,
          'ROUTE',
          :route_id,
          JSON_OBJECT('suggested_actions', JSON_ARRAY('SUBSTITUTE_AIRCRAFT', 'DELAY_FLIGHT', 'CANCEL_FLIGHT'))
        )
    ");
    $mail->execute([
        'company_id' => $companyId,
        'title' => $title,
        'body' => $body,
        'route_id' => (int)$route['route_id'],
    ]);
    $messageId = (int)$pdo->lastInsertId();

    $pdo->prepare("
        INSERT INTO route_dispatch_attempts (
          route_id,
          company_id,
          scheduled_departure_at_utc,
          result,
          reason,
          reputation_delta,
          budget_delta,
          currency_code,
          mailbox_message_id
        ) VALUES (
          :route_id,
          :company_id,
          :scheduled_departure,
          :result,
          :reason,
          :reputation_delta,
          :budget_delta,
          :currency_code,
          :message_id
        )
    ")->execute([
        'route_id' => (int)$route['route_id'],
        'company_id' => $companyId,
        'scheduled_departure' => $scheduledDeparture,
        'result' => $result,
        'reason' => $reason,
        'reputation_delta' => $reputationDelta,
        'budget_delta' => number_format($budgetDelta, 2, '.', ''),
        'currency_code' => $route['currency_code'],
        'message_id' => $messageId,
    ]);

    $pdo->prepare("
        UPDATE companies
        SET
          budget_amount = budget_amount + :budget_delta,
          reputation_score = GREATEST(0, reputation_score + :reputation_delta)
        WHERE id = :company_id
    ")->execute([
        'budget_delta' => number_format($budgetDelta, 2, '.', ''),
        'reputation_delta' => $reputationDelta,
        'company_id' => $companyId,
    ]);

    $pdo->prepare("
        UPDATE company_routes
        SET
          missed_dispatch_count = missed_dispatch_count + 1,
          last_dispatch_attempt_at_utc = UTC_TIMESTAMP(),
          last_dispatch_result = :result
        WHERE id = :route_id
          AND company_id = :company_id
    ")->execute([
        'result' => $result,
        'route_id' => (int)$route['route_id'],
        'company_id' => $companyId,
    ]);

    return [
        'route_id' => (int)$route['route_id'],
        'result' => $result,
        'reason' => $reason,
        'mailbox_message_id' => $messageId,
        'reputation_delta' => $reputationDelta,
        'budget_delta' => number_format($budgetDelta, 2, '.', ''),
    ];
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
    return (float)($staff['pilot_salary'] ?? 0) + ($revenue * (float)($staff['pilot_revenue_share'] ?? 0) / 100.0);
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
            SET status = 'COMPLETED', actual_arrival_at_utc = UTC_TIMESTAMP()
            WHERE id = :id
        ")->execute(['id' => (int)$flight['id']]);

        $pdo->prepare("
            UPDATE company_aircraft
            SET status = 'AVAILABLE', current_airport_icao_code = :destination
            WHERE id = :aircraft_id AND company_id = :company_id
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
