<?php
declare(strict_types=1);

/**
 * Maintenance simulation helpers.
 *
 * These functions make maintenance time-based: once an IN_PROGRESS
 * maintenance/fault event reaches its estimated completion time, the game
 * completes it automatically, releases the aircraft and creates a mailbox
 * notification for the player.
 */
function complete_due_maintenance(PDO $pdo, int $companyId): array
{
    $ownsTransaction = !$pdo->inTransaction();

    if ($ownsTransaction) {
        $pdo->beginTransaction();
    }

    try {
        $stmt = $pdo->prepare("
            SELECT
              e.id AS event_id,
              e.aircraft_id,
              e.event_type,
              e.severity,
              e.title,
              e.description,
              e.assigned_technician_id,
              e.mailbox_message_id,
              e.estimated_completed_at_utc,
              ca.registration_code,
              ca.status AS aircraft_status,
              ca.condition_percent,
              am.manufacturer,
              am.model_name,
              ca.currency_code
            FROM aircraft_operational_events e
            JOIN company_aircraft ca
              ON ca.id = e.aircraft_id
            JOIN aircraft_models am
              ON am.id = ca.aircraft_model_id
            WHERE e.company_id = :company_id
              AND e.status = 'IN_PROGRESS'
              AND e.estimated_completed_at_utc IS NOT NULL
              AND e.estimated_completed_at_utc <= UTC_TIMESTAMP()
              AND e.event_type IN (
                'ROUTINE_MAINTENANCE_DUE',
                'CONDITION_WARNING',
                'GROUND_FAULT_MINOR',
                'GROUND_FAULT_MAJOR'
              )
            ORDER BY e.estimated_completed_at_utc, e.id
            FOR UPDATE
        ");
        $stmt->execute(['company_id' => $companyId]);
        $events = $stmt->fetchAll();

        $completed = [];

        foreach ($events as $event) {
            $aircraftId = (int)$event['aircraft_id'];
            $eventId = (int)$event['event_id'];
            $registration = (string)$event['registration_code'];

            $pdo->prepare("
                UPDATE company_aircraft
                SET
                  status = 'AVAILABLE',
                  condition_percent = 100.00,
                  airframe_hours = 0.00,
                  cycles_count = 0
                WHERE id = :aircraft_id
                  AND company_id = :company_id
                  AND status = 'MAINTENANCE'
            ")->execute([
                'aircraft_id' => $aircraftId,
                'company_id' => $companyId,
            ]);

            $pdo->prepare("
                UPDATE aircraft_operational_events
                SET
                  status = 'COMPLETED',
                  completed_at_utc = UTC_TIMESTAMP(),
                  condition_percent_after = 100.00
                WHERE id = :event_id
                  AND company_id = :company_id
                  AND status = 'IN_PROGRESS'
            ")->execute([
                'event_id' => $eventId,
                'company_id' => $companyId,
            ]);

            if (!empty($event['mailbox_message_id'])) {
                $pdo->prepare("
                    UPDATE game_mailbox_messages
                    SET
                      status = IF(status IN ('UNREAD', 'READ'), 'RESOLVED', status),
                      resolved_at_utc = COALESCE(resolved_at_utc, UTC_TIMESTAMP())
                    WHERE id = :message_id
                      AND company_id = :company_id
                ")->execute([
                    'message_id' => (int)$event['mailbox_message_id'],
                    'company_id' => $companyId,
                ]);
            }

            $title = $registration . ' maintenance completed';
            $body = sprintf(
                'Maintenance completed for %s %s (%s). The aircraft is now available again with condition restored to 100%%.',
                $event['manufacturer'],
                $event['model_name'],
                $registration
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
                  'SYSTEM',
                  'INFO',
                  'UNREAD',
                  :title,
                  :body,
                  'AIRCRAFT',
                  :aircraft_id,
                  JSON_OBJECT(
                    'completed_maintenance_event_id', :event_id,
                    'suggested_actions', JSON_ARRAY('RETURN_TO_SERVICE', 'PLAN_NEXT_FLIGHT')
                  )
                )
            ");
            $mail->execute([
                'company_id' => $companyId,
                'title' => $title,
                'body' => $body,
                'aircraft_id' => $aircraftId,
                'event_id' => $eventId,
            ]);

            $completed[] = [
                'event_id' => $eventId,
                'aircraft_id' => $aircraftId,
                'registration_code' => $registration,
                'status' => 'AVAILABLE',
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

function maintenance_dispatch_guard_sql(string $aircraftAlias = 'ca', string $modelAlias = 'am'): string
{
    return "
      AND {$aircraftAlias}.status IN ('AVAILABLE', 'PARKED')
      AND {$aircraftAlias}.condition_percent > COALESCE((
        SELECT mp.condition_grounding_threshold_percent
        FROM aircraft_maintenance_profiles mp
        WHERE mp.aircraft_model_id = {$modelAlias}.id
        LIMIT 1
      ), 45.00)
      AND NOT EXISTS (
        SELECT 1
        FROM aircraft_operational_events me
        WHERE me.company_id = {$aircraftAlias}.company_id
          AND me.aircraft_id = {$aircraftAlias}.id
          AND me.status = 'IN_PROGRESS'
          AND me.event_type IN (
            'ROUTINE_MAINTENANCE_DUE',
            'CONDITION_WARNING',
            'GROUND_FAULT_MINOR',
            'GROUND_FAULT_MAJOR'
          )
      )
    ";
}
