<?php
declare(strict_types=1);

require __DIR__ . '/../../lib/bootstrap.php';
require __DIR__ . '/../../lib/session.php';
require_once __DIR__ . '/../../lib/maintenance-engine.php';

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    json_response(['error' => 'METHOD_NOT_ALLOWED'], 405);
}

$session = require_auth_session();
$companyId = $session['company_id'];

$pdo = db();

try {
    $pdo->beginTransaction();

    $completedMaintenance = complete_due_maintenance($pdo, (int)$companyId);

    $stmt = $pdo->prepare("
        SELECT *
        FROM v_aircraft_maintenance_status
        WHERE company_id = :company_id
          AND maintenance_state <> 'OK'
    ");
    $stmt->execute(['company_id' => $companyId]);
    $rows = $stmt->fetchAll();

    $created = [];

    foreach ($rows as $row) {
        $existing = $pdo->prepare("
            SELECT id
            FROM aircraft_operational_events
            WHERE company_id = :company_id
              AND aircraft_id = :aircraft_id
              AND status IN ('OPEN', 'IN_PROGRESS')
              AND event_type IN ('ROUTINE_MAINTENANCE_DUE', 'CONDITION_WARNING')
            LIMIT 1
        ");
        $existing->execute([
            'company_id' => $companyId,
            'aircraft_id' => (int)$row['aircraft_id'],
        ]);

        if ($existing->fetch()) {
            continue;
        }

        $severity = $row['maintenance_state'] === 'GROUNDED_REQUIRED' ? 'CRITICAL' : 'WARNING';
        $eventType = $row['maintenance_state'] === 'CONDITION_WARNING'
            ? 'CONDITION_WARNING'
            : 'ROUTINE_MAINTENANCE_DUE';

        $title = $row['registration_code'] . ' maintenance attention required';
        $body = sprintf(
            "%s %s (%s) requires maintenance attention. State: %s. Condition: %.2f%%. Required technician license: %s.",
            $row['manufacturer'],
            $row['model_name'],
            $row['registration_code'],
            $row['maintenance_state'],
            (float)$row['condition_percent'],
            $row['technician_license_required'] ?? 'N/A'
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
            'aircraft_id' => (int)$row['aircraft_id'],
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
              estimated_completed_at_utc,
              mailbox_message_id
            ) VALUES (
              :company_id,
              :aircraft_id,
              :event_type,
              :severity,
              'OPEN',
              :title,
              :description,
              :condition_before,
              :condition_after,
              :license,
              DATE_ADD(UTC_TIMESTAMP(), INTERVAL :duration HOUR),
              :message_id
            )
        ");
        $event->execute([
            'company_id' => $companyId,
            'aircraft_id' => (int)$row['aircraft_id'],
            'event_type' => $eventType,
            'severity' => $severity,
            'title' => $title,
            'description' => $body,
            'condition_before' => $row['condition_percent'],
            'condition_after' => $row['condition_percent'],
            'license' => $row['technician_license_required'],
            'duration' => (int)($row['routine_maintenance_duration_hours'] ?? 8),
            'message_id' => $messageId,
        ]);

        $created[] = [
            'message_id' => $messageId,
            'aircraft_id' => (int)$row['aircraft_id'],
            'registration_code' => $row['registration_code'],
            'maintenance_state' => $row['maintenance_state'],
        ];
    }

    $pdo->commit();

    json_response([
        'completed_count' => count($completedMaintenance),
        'completed' => $completedMaintenance,
        'created_count' => count($created),
        'created' => $created,
    ]);
} catch (Throwable $exception) {
    if ($pdo->inTransaction()) {
        $pdo->rollBack();
    }

    json_response([
        'error' => 'DATABASE_ERROR',
        'message' => 'Unable to run maintenance check.',
    ], 500);
}
