<?php
declare(strict_types=1);

require_once __DIR__ . '/reputation.php';

/**
 * Complete all due IN_FLIGHT flights for a company.
 *
 * This is the single canonical flight completion function.
 *
 * It always applies:
 * - scheduled_flight_instances: IN_FLIGHT -> COMPLETED
 * - company_aircraft: AVAILABLE at destination
 * - companies: budget update
 * - reputation rules
 * - aircraft wear: hours, cycles, condition
 * - mailbox / operational event if maintenance warning/grounding threshold is reached
 *
 * Safe to call inside an existing transaction or standalone.
 */
function complete_due_flights(PDO $pdo, int $companyId): array
{
    $ownsTransaction = !$pdo->inTransaction();

    if ($ownsTransaction) {
        $pdo->beginTransaction();
    }

    try {
        $stmt = $pdo->prepare("
            SELECT
              f.id,
              f.aircraft_id,
              f.destination_airport_icao_code,
              f.profit_amount,
              f.actual_departure_at_utc,
              f.scheduled_departure_at_utc,
              f.scheduled_arrival_at_utc,
              f.flight_code,
              f.origin_airport_icao_code,
              f.destination_airport_icao_code,

              ca.registration_code,
              ca.condition_percent,
              ca.airframe_hours,
              ca.cycles_count,

              am.manufacturer,
              am.model_name,
              am.model_code,

              mp.condition_loss_per_flight_percent,
              mp.condition_warning_threshold_percent,
              mp.condition_grounding_threshold_percent,
              mp.technician_license_required
            FROM scheduled_flight_instances f
            JOIN company_aircraft ca
              ON ca.id = f.aircraft_id
            JOIN aircraft_models am
              ON am.id = ca.aircraft_model_id
            LEFT JOIN aircraft_maintenance_profiles mp
              ON mp.aircraft_model_id = am.id
            WHERE f.company_id = :company_id
              AND f.status = 'IN_FLIGHT'
              AND f.scheduled_arrival_at_utc <= UTC_TIMESTAMP()
            ORDER BY f.scheduled_arrival_at_utc
            FOR UPDATE
        ");
        $stmt->execute(['company_id' => $companyId]);
        $flights = $stmt->fetchAll();

        $completed = [];

        foreach ($flights as $flight) {
            $flightId = (int)$flight['id'];
            $aircraftId = (int)$flight['aircraft_id'];
            $profit = (float)$flight['profit_amount'];

            $durationHours = calculate_completed_flight_hours($flight);
            $conditionLoss = calculate_condition_loss($flight, $durationHours);
            $conditionBefore = (float)$flight['condition_percent'];
            $conditionAfter = max(0.0, $conditionBefore - $conditionLoss);

            $pdo->prepare("
                UPDATE scheduled_flight_instances
                SET
                  status = 'COMPLETED',
                  actual_arrival_at_utc = UTC_TIMESTAMP()
                WHERE id = :id
                  AND company_id = :company_id
                  AND status = 'IN_FLIGHT'
            ")->execute([
                'id' => $flightId,
                'company_id' => $companyId,
            ]);

            $pdo->prepare("
                UPDATE company_aircraft
                SET
                  status = 'AVAILABLE',
                  current_airport_icao_code = :destination,
                  airframe_hours = airframe_hours + :duration_hours,
                  cycles_count = cycles_count + 1,
                  condition_percent = :condition_after
                WHERE id = :aircraft_id
                  AND company_id = :company_id
            ")->execute([
                'destination' => $flight['destination_airport_icao_code'],
                'duration_hours' => number_format($durationHours, 4, '.', ''),
                'condition_after' => number_format($conditionAfter, 2, '.', ''),
                'aircraft_id' => $aircraftId,
                'company_id' => $companyId,
            ]);

            $pdo->prepare("
                UPDATE companies
                SET budget_amount = budget_amount + :profit
                WHERE id = :company_id
            ")->execute([
                'profit' => number_format($profit, 2, '.', ''),
                'company_id' => $companyId,
            ]);

            $reputationResult = apply_reputation_event(
                $pdo,
                $companyId,
                $profit > 0 ? 'FLIGHT_COMPLETED_PROFITABLE' : 'FLIGHT_COMPLETED_BREAK_EVEN_OR_LOSS',
                'FLIGHT',
                $flightId,
                $profit > 0
                    ? 'Flight completed successfully with positive profit.'
                    : 'Flight completed successfully but did not generate positive profit.'
            );

            $maintenanceEvent = maybe_create_maintenance_event_after_flight(
                $pdo,
                $companyId,
                $flight,
                $conditionBefore,
                $conditionAfter,
                $flightId
            );

            $completed[] = [
                'flight_id' => $flightId,
                'flight_code' => $flight['flight_code'],
                'aircraft_id' => $aircraftId,
                'registration_code' => $flight['registration_code'],
                'destination_airport_icao_code' => $flight['destination_airport_icao_code'],
                'profit_amount' => number_format($profit, 2, '.', ''),
                'duration_hours' => number_format($durationHours, 2, '.', ''),
                'condition_before' => number_format($conditionBefore, 2, '.', ''),
                'condition_after' => number_format($conditionAfter, 2, '.', ''),
                'condition_loss' => number_format($conditionLoss, 2, '.', ''),
                'reputation' => $reputationResult,
                'maintenance_event' => $maintenanceEvent,
            ];
        }

        if ($ownsTransaction) {
            $pdo->commit();
        }

        return $completed;
    } catch (Throwable $exception) {
        if ($ownsTransaction && $pdo->inTransaction()) {
            $pdo->rollBack();
        }

        throw $exception;
    }
}

function calculate_completed_flight_hours(array $flight): float
{
    $departure = $flight['actual_departure_at_utc']
        ?: $flight['scheduled_departure_at_utc'];

    $arrival = $flight['scheduled_arrival_at_utc'];

    $departureTs = strtotime((string)$departure . ' UTC');
    $arrivalTs = strtotime((string)$arrival . ' UTC');

    if (!$departureTs || !$arrivalTs || $arrivalTs <= $departureTs) {
        return 0.25;
    }

    return max(0.25, ($arrivalTs - $departureTs) / 3600.0);
}

function calculate_condition_loss(array $flight, float $durationHours): float
{
    $baseLoss = $flight['condition_loss_per_flight_percent'] !== null
        ? (float)$flight['condition_loss_per_flight_percent']
        : 0.40;

    /*
     * Slightly scale wear with duration, while keeping short test flights meaningful.
     */
    $durationFactor = max(1.0, $durationHours);

    return round($baseLoss * $durationFactor, 2);
}

function maybe_create_maintenance_event_after_flight(
    PDO $pdo,
    int $companyId,
    array $flight,
    float $conditionBefore,
    float $conditionAfter,
    int $flightId
): ?array {
    $warningThreshold = $flight['condition_warning_threshold_percent'] !== null
        ? (float)$flight['condition_warning_threshold_percent']
        : 70.0;

    $groundingThreshold = $flight['condition_grounding_threshold_percent'] !== null
        ? (float)$flight['condition_grounding_threshold_percent']
        : 45.0;

    if ($conditionAfter > $warningThreshold) {
        return null;
    }

    $aircraftId = (int)$flight['aircraft_id'];

    $existing = $pdo->prepare("
        SELECT id
        FROM aircraft_operational_events
        WHERE company_id = :company_id
          AND aircraft_id = :aircraft_id
          AND status IN ('OPEN', 'IN_PROGRESS')
          AND event_type IN ('CONDITION_WARNING', 'ROUTINE_MAINTENANCE_DUE')
        LIMIT 1
    ");
    $existing->execute([
        'company_id' => $companyId,
        'aircraft_id' => $aircraftId,
    ]);

    if ($existing->fetch()) {
        return null;
    }

    $isGrounded = $conditionAfter <= $groundingThreshold;
    $severity = $isGrounded ? 'CRITICAL' : 'WARNING';
    $eventType = $isGrounded ? 'ROUTINE_MAINTENANCE_DUE' : 'CONDITION_WARNING';

    $title = sprintf(
        '%s maintenance attention required',
        $flight['registration_code']
    );

    $body = sprintf(
        '%s %s (%s) completed flight %s and condition changed from %.2f%% to %.2f%%. %s',
        $flight['manufacturer'],
        $flight['model_name'],
        $flight['registration_code'],
        $flight['flight_code'],
        $conditionBefore,
        $conditionAfter,
        $isGrounded
            ? 'Aircraft should be grounded until maintenance is completed.'
            : 'Maintenance should be planned before condition becomes critical.'
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
          'MAINTENANCE_REQUIRED',
          :severity,
          'UNREAD',
          :title,
          :body,
          'AIRCRAFT',
          :aircraft_id,
          JSON_OBJECT(
            'suggested_actions',
            JSON_ARRAY('SCHEDULE_MAINTENANCE', 'SUBSTITUTE_AIRCRAFT', 'DELAY_FLIGHT')
          )
        )
    ");
    $mail->execute([
        'company_id' => $companyId,
        'severity' => $severity,
        'title' => $title,
        'body' => $body,
        'aircraft_id' => $aircraftId,
    ]);

    $messageId = (int)$pdo->lastInsertId();

    $event = $pdo->prepare("
        INSERT INTO aircraft_operational_events (
          company_id,
          aircraft_id,
          flight_instance_id,
          event_type,
          severity,
          status,
          title,
          description,
          condition_percent_before,
          condition_percent_after,
          required_technician_license,
          mailbox_message_id
        ) VALUES (
          :company_id,
          :aircraft_id,
          :flight_id,
          :event_type,
          :severity,
          'OPEN',
          :title,
          :description,
          :condition_before,
          :condition_after,
          :license,
          :message_id
        )
    ");
    $event->execute([
        'company_id' => $companyId,
        'aircraft_id' => $aircraftId,
        'flight_id' => $flightId,
        'event_type' => $eventType,
        'severity' => $severity,
        'title' => $title,
        'description' => $body,
        'condition_before' => number_format($conditionBefore, 2, '.', ''),
        'condition_after' => number_format($conditionAfter, 2, '.', ''),
        'license' => $flight['technician_license_required'],
        'message_id' => $messageId,
    ]);

    if ($isGrounded) {
        $pdo->prepare("
            UPDATE company_aircraft
            SET status = 'MAINTENANCE'
            WHERE id = :aircraft_id
              AND company_id = :company_id
        ")->execute([
            'aircraft_id' => $aircraftId,
            'company_id' => $companyId,
        ]);
    }

    return [
        'event_id' => (int)$pdo->lastInsertId(),
        'message_id' => $messageId,
        'event_type' => $eventType,
        'severity' => $severity,
    ];
}
