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

if ($aircraftId <= 0) {
    json_response(['error' => 'VALIDATION_ERROR', 'message' => 'aircraft_id is required.'], 422);
}

$pdo = db();

try {
    $pdo->beginTransaction();

    $aircraftStmt = $pdo->prepare("
        SELECT id, status
        FROM company_aircraft
        WHERE id = :aircraft_id
          AND company_id = :company_id
        LIMIT 1
        FOR UPDATE
    ");
    $aircraftStmt->execute([
        'aircraft_id' => $aircraftId,
        'company_id' => $companyId,
    ]);
    $aircraft = $aircraftStmt->fetch();

    if (!$aircraft) {
        $pdo->rollBack();
        json_response(['error' => 'AIRCRAFT_NOT_FOUND'], 404);
    }

    if ($aircraft['status'] !== 'MAINTENANCE') {
        $pdo->rollBack();
        json_response(['error' => 'AIRCRAFT_NOT_IN_MAINTENANCE'], 409);
    }

    $eventStmt = $pdo->prepare("
        SELECT id
        FROM aircraft_operational_events
        WHERE company_id = :company_id
          AND aircraft_id = :aircraft_id
          AND status = 'IN_PROGRESS'
        ORDER BY started_at_utc DESC
        LIMIT 1
        FOR UPDATE
    ");
    $eventStmt->execute([
        'company_id' => $companyId,
        'aircraft_id' => $aircraftId,
    ]);
    $eventId = (int)($eventStmt->fetchColumn() ?: 0);

    $pdo->prepare("
        UPDATE company_aircraft
        SET
          status = 'AVAILABLE',
          condition_percent = 100.00,
          airframe_hours = 0.00,
          cycles_count = 0
        WHERE id = :aircraft_id
          AND company_id = :company_id
    ")->execute([
        'aircraft_id' => $aircraftId,
        'company_id' => $companyId,
    ]);

    if ($eventId > 0) {
        $pdo->prepare("
            UPDATE aircraft_operational_events
            SET
              status = 'COMPLETED',
              completed_at_utc = UTC_TIMESTAMP(),
              condition_percent_after = 100.00
            WHERE id = :event_id
        ")->execute(['event_id' => $eventId]);
    }

    $pdo->commit();

    json_response([
        'aircraft_id' => $aircraftId,
        'event_id' => $eventId ?: null,
        'status' => 'AVAILABLE',
        'condition_percent' => '100.00',
    ]);
} catch (Throwable $exception) {
    if ($pdo->inTransaction()) {
        $pdo->rollBack();
    }

    json_response(['error' => 'DATABASE_ERROR', 'message' => 'Unable to complete maintenance.'], 500);
}
