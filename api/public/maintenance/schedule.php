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

$aircraftId = (int)($payload['aircraft_id'] ?? 0);
$force = (bool)($payload['force'] ?? false);

if ($aircraftId <= 0) {
    json_response(['error' => 'VALIDATION_ERROR', 'message' => 'aircraft_id is required.'], 422);
}

$pdo = db();

try {
    $pdo->beginTransaction();

    $aircraft = fetch_aircraft_for_update($pdo, $companyId, $aircraftId);

    if (!$aircraft) {
        $pdo->rollBack();
        json_response(['error' => 'AIRCRAFT_NOT_FOUND'], 404);
    }

    if ($aircraft['aircraft_status'] === 'IN_FLIGHT') {
        $pdo->rollBack();
        json_response([
            'error' => 'AIRCRAFT_IN_FLIGHT',
            'message' => 'Maintenance can only start when the aircraft is on the ground.',
        ], 409);
    }

    if ($aircraft['aircraft_status'] === 'MAINTENANCE') {
        $pdo->rollBack();
        json_response(['error' => 'MAINTENANCE_ALREADY_IN_PROGRESS'], 409);
    }

    $company = fetch_company_for_update($pdo, $companyId);

    if (!$company) {
        $pdo->rollBack();
        json_response(['error' => 'COMPANY_NOT_FOUND'], 404);
    }

    $license = $aircraft['technician_license_required'] ?? null;
    $durationHours = max(1, (int)$aircraft['routine_maintenance_duration_hours']);
    $maintenanceCost = max(0.0, (float)($aircraft['routine_maintenance_cost_amount'] ?? 0.0));
    $currencyCode = (string)($company['currency_code'] ?? $aircraft['currency_code'] ?? 'EUR');

    if ($maintenanceCost > (float)$company['budget_amount']) {
        $pdo->rollBack();
        json_response([
            'error' => 'INSUFFICIENT_BUDGET',
            'message' => sprintf(
                'Maintenance cannot start: required budget is %.2f %s, available budget is %.2f %s.',
                $maintenanceCost,
                $currencyCode,
                (float)$company['budget_amount'],
                $currencyCode
            ),
            'required_amount' => number_format($maintenanceCost, 2, '.', ''),
            'available_budget' => number_format((float)$company['budget_amount'], 2, '.', ''),
            'currency_code' => $currencyCode,
        ], 409);
    }


    $technician = find_available_technician($pdo, $companyId, $license, $durationHours);

    if (!$technician) {
        $pdo->rollBack();
        json_response([
            'error' => 'NO_AVAILABLE_QUALIFIED_TECHNICIAN',
            'message' => 'No qualified technician is currently available for the full maintenance window.',
            'required_license' => $license,
        ], 409);
    }

    $impact = calculate_schedule_impact($pdo, $companyId, $aircraftId, $durationHours);

    if ($impact['has_risk'] && !$force) {
        $pdo->rollBack();
        json_response([
            'error' => 'MAINTENANCE_OVERLAPS_NEXT_FLIGHT',
            'message' => 'Maintenance may overlap a scheduled flight. Confirm with force=true to accept delay/penalty risk.',
            'impact' => $impact,
        ], 409);
    }

    $title = $aircraft['registration_code'] . ' maintenance started';
    $description = sprintf(
        'Routine maintenance started for %s %s (%s). Technician: %s. Expected duration: %d hours. Cost: %.2f %s.',
        $aircraft['manufacturer'],
        $aircraft['model_name'],
        $aircraft['registration_code'],
        $technician['display_name'],
        $durationHours,
        $maintenanceCost,
        $currencyCode
    );

    if ($impact['has_risk']) {
        $description .= sprintf(
            ' Warning: next scheduled route %s → %s may be delayed by about %d minutes. Estimated penalty: %.2f %s.',
            $impact['origin_airport_icao_code'],
            $impact['destination_airport_icao_code'],
            $impact['delay_risk_minutes'],
            $impact['estimated_penalty_amount'],
            $aircraft['currency_code']
        );
    }

    $messageType = $impact['has_risk'] ? 'DISPATCH_BLOCKED' : 'MAINTENANCE_REQUIRED';
    $severity = $impact['has_risk'] ? 'WARNING' : 'INFO';

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
          :message_type,
          :severity,
          'UNREAD',
          :title,
          :body,
          'AIRCRAFT',
          :aircraft_id,
          JSON_OBJECT(
            'suggested_actions',
            IF(:has_risk = 1,
              JSON_ARRAY('ACCEPT_DELAY', 'SUBSTITUTE_AIRCRAFT', 'CANCEL_MAINTENANCE'),
              JSON_ARRAY('WAIT_COMPLETION')
            ),
            'delay_risk_minutes',
            :delay_risk_minutes,
            'estimated_penalty_amount',
            :estimated_penalty_amount,
            'maintenance_cost_amount',
            :maintenance_cost_amount,
            'currency_code',
            :currency_code
          )
        )
    ");
    $mail->execute([
        'company_id' => $companyId,
        'message_type' => $messageType,
        'severity' => $severity,
        'title' => $title,
        'body' => $description,
        'aircraft_id' => $aircraftId,
        'has_risk' => $impact['has_risk'] ? 1 : 0,
        'delay_risk_minutes' => $impact['delay_risk_minutes'],
        'estimated_penalty_amount' => number_format($impact['estimated_penalty_amount'], 2, '.', ''),
        'maintenance_cost_amount' => number_format($maintenanceCost, 2, '.', ''),
        'currency_code' => $currencyCode,
    ]);
    $messageId = (int)$pdo->lastInsertId();

    $event = $pdo->prepare("
        INSERT INTO aircraft_operational_events (
          company_id,
          aircraft_id,
          event_type,
          severity,
          status,
          title,
          description,
          condition_percent_before,
          condition_percent_after,
          required_technician_license,
          assigned_technician_id,
          delay_risk_minutes,
          estimated_penalty_amount,
          cost_amount,
          cost_currency_code,
          responsibility_type,
          estimated_completed_at_utc,
          mailbox_message_id
        ) VALUES (
          :company_id,
          :aircraft_id,
          'ROUTINE_MAINTENANCE_DUE',
          :severity,
          'IN_PROGRESS',
          :title,
          :description,
          :condition_before,
          100.00,
          :license,
          :technician_id,
          :delay_risk_minutes,
          :estimated_penalty_amount,
          :cost_amount,
          :cost_currency_code,
          'COMPANY_FAULT',
          DATE_ADD(UTC_TIMESTAMP(), INTERVAL :duration HOUR),
          :message_id
        )
    ");
    $event->execute([
        'company_id' => $companyId,
        'aircraft_id' => $aircraftId,
        'severity' => $severity,
        'title' => $title,
        'description' => $description,
        'condition_before' => $aircraft['condition_percent'],
        'license' => $license,
        'technician_id' => (int)$technician['id'],
        'delay_risk_minutes' => $impact['delay_risk_minutes'],
        'estimated_penalty_amount' => number_format($impact['estimated_penalty_amount'], 2, '.', ''),
        'cost_amount' => number_format($maintenanceCost, 2, '.', ''),
        'cost_currency_code' => $currencyCode,
        'duration' => $durationHours,
        'message_id' => $messageId,
    ]);

    $eventId = (int)$pdo->lastInsertId();

    $pdo->prepare("
        UPDATE companies
        SET budget_amount = budget_amount - :maintenance_cost
        WHERE id = :company_id
    ")->execute([
        'maintenance_cost' => number_format($maintenanceCost, 2, '.', ''),
        'company_id' => $companyId,
    ]);

    $pdo->prepare("
        INSERT INTO company_financial_events (
          company_id,
          event_type,
          amount,
          currency_code,
          description,
          related_entity_type,
          related_entity_id
        ) VALUES (
          :company_id,
          'AIRCRAFT_MAINTENANCE_COST',
          :amount,
          :currency_code,
          :description,
          'AIRCRAFT_OPERATIONAL_EVENT',
          :event_id
        )
    ")->execute([
        'company_id' => $companyId,
        'amount' => number_format(-$maintenanceCost, 2, '.', ''),
        'currency_code' => $currencyCode,
        'description' => sprintf(
            'Routine maintenance started for %s. Cost paid at maintenance start.',
            $aircraft['registration_code']
        ),
        'event_id' => $eventId,
    ]);

    $pdo->prepare("
        UPDATE company_aircraft
        SET status = 'MAINTENANCE'
        WHERE id = :aircraft_id
          AND company_id = :company_id
    ")->execute([
        'aircraft_id' => $aircraftId,
        'company_id' => $companyId,
    ]);

    $pdo->commit();

    json_response([
        'event_id' => $eventId,
        'message_id' => $messageId,
        'aircraft_id' => $aircraftId,
        'status' => 'MAINTENANCE',
        'assigned_technician_id' => (int)$technician['id'],
        'assigned_technician_name' => $technician['display_name'],
        'estimated_duration_hours' => $durationHours,
        'maintenance_cost_amount' => number_format($maintenanceCost, 2, '.', ''),
        'currency_code' => $currencyCode,
        'impact' => $impact,
    ], 201);
} catch (Throwable $exception) {
    if ($pdo->inTransaction()) {
        $pdo->rollBack();
    }

    json_response([
        'error' => 'DATABASE_ERROR',
        'message' => 'Unable to start maintenance.',
    ], 500);
}

function fetch_company_for_update(PDO $pdo, int $companyId): ?array
{
    $stmt = $pdo->prepare("
        SELECT id, company_name, currency_code, budget_amount
        FROM companies
        WHERE id = :company_id
        LIMIT 1
        FOR UPDATE
    ");
    $stmt->execute(['company_id' => $companyId]);

    $row = $stmt->fetch();
    return $row ?: null;
}

function fetch_aircraft_for_update(PDO $pdo, int $companyId, int $aircraftId): ?array
{
    $stmt = $pdo->prepare("
        SELECT *
        FROM v_company_aircraft_maintenance_detail
        WHERE company_id = :company_id
          AND aircraft_id = :aircraft_id
        LIMIT 1
    ");
    $stmt->execute([
        'company_id' => $companyId,
        'aircraft_id' => $aircraftId,
    ]);

    $row = $stmt->fetch();
    return $row ?: null;
}

function find_available_technician(PDO $pdo, int $companyId, ?string $licenseCode, int $durationHours): ?array
{
    $sql = "
        SELECT s.id, s.display_name
        FROM company_staff s
        WHERE s.company_id = :company_id
          AND s.staff_role = 'TECHNICIAN'
          AND s.employment_status = 'ACTIVE'
    ";

    $params = ['company_id' => $companyId];

    if ($licenseCode !== null && $licenseCode !== '') {
        $sql .= "
          AND EXISTS (
            SELECT 1
            FROM company_staff_licenses l
            WHERE l.company_staff_id = s.id
              AND l.license_code = :license_code
          )
        ";
        $params['license_code'] = $licenseCode;
    }

    $sql .= "
      AND NOT EXISTS (
        SELECT 1
        FROM aircraft_operational_events e
        WHERE e.company_id = s.company_id
          AND e.assigned_technician_id = s.id
          AND e.status = 'IN_PROGRESS'
          AND e.estimated_completed_at_utc > UTC_TIMESTAMP()
      )
      ORDER BY s.reliability_score DESC, s.fatigue_score ASC, s.id
      LIMIT 1
    ";

    $stmt = $pdo->prepare($sql);
    $stmt->execute($params);

    $row = $stmt->fetch();
    return $row ?: null;
}

function calculate_schedule_impact(PDO $pdo, int $companyId, int $aircraftId, int $durationHours): array
{
    $maintenanceEndSql = "DATE_ADD(UTC_TIMESTAMP(), INTERVAL :duration HOUR)";

    $stmt = $pdo->prepare("
        SELECT
          r.id AS route_id,
          r.origin_airport_icao_code,
          r.destination_airport_icao_code,
          r.scheduled_departure_time_utc,
          r.ticket_price,
          r.currency_code,
          TIMESTAMP(CURRENT_DATE(), r.scheduled_departure_time_utc) AS scheduled_departure_at_utc
        FROM company_routes r
        WHERE r.company_id = :company_id
          AND r.status = 'ACTIVE'
          AND r.aircraft_id = :aircraft_id
          AND TIMESTAMP(CURRENT_DATE(), r.scheduled_departure_time_utc) >= UTC_TIMESTAMP()
        ORDER BY TIMESTAMP(CURRENT_DATE(), r.scheduled_departure_time_utc)
        LIMIT 1
    ");
    $stmt->execute([
        'company_id' => $companyId,
        'aircraft_id' => $aircraftId,
    ]);
    $route = $stmt->fetch();

    if (!$route) {
        return [
            'has_risk' => false,
            'route_id' => null,
            'delay_risk_minutes' => 0,
            'estimated_penalty_amount' => 0.00,
        ];
    }

    $timeStmt = $pdo->prepare("
        SELECT
          TIMESTAMPDIFF(
            MINUTE,
            TIMESTAMP(CURRENT_DATE(), :departure_time),
            DATE_ADD(UTC_TIMESTAMP(), INTERVAL :duration HOUR)
          ) AS overlap_minutes
    ");
    $timeStmt->execute([
        'departure_time' => $route['scheduled_departure_time_utc'],
        'duration' => $durationHours,
    ]);

    $overlap = max(0, (int)$timeStmt->fetchColumn());

    if ($overlap <= 0) {
        return [
            'has_risk' => false,
            'route_id' => (int)$route['route_id'],
            'origin_airport_icao_code' => $route['origin_airport_icao_code'],
            'destination_airport_icao_code' => $route['destination_airport_icao_code'],
            'scheduled_departure_at_utc' => $route['scheduled_departure_at_utc'],
            'delay_risk_minutes' => 0,
            'estimated_penalty_amount' => 0.00,
            'currency_code' => $route['currency_code'],
        ];
    }

    /*
     * Simple first penalty model:
     * - base passenger disruption cost: ticket price * 4 assumed pax * 35%
     * - delay cost: 8 per minute
     * This will later be replaced by actual booked passenger count/load factor.
     */
    $estimatedPenalty = ((float)$route['ticket_price'] * 4 * 0.35) + ($overlap * 8.0);

    return [
        'has_risk' => true,
        'route_id' => (int)$route['route_id'],
        'origin_airport_icao_code' => $route['origin_airport_icao_code'],
        'destination_airport_icao_code' => $route['destination_airport_icao_code'],
        'scheduled_departure_at_utc' => $route['scheduled_departure_at_utc'],
        'delay_risk_minutes' => $overlap,
        'estimated_penalty_amount' => round($estimatedPenalty, 2),
        'currency_code' => $route['currency_code'],
    ];
}
