<?php
declare(strict_types=1);

require __DIR__ . '/../../lib/bootstrap.php';
require __DIR__ . '/../../lib/session.php';
require_once __DIR__ . '/../../lib/scheduled-service-dispatcher.php';

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    json_response(['error' => 'METHOD_NOT_ALLOWED'], 405);
}

$session = require_auth_session();
$companyId = (int)$session['company_id'];
$payload = read_json_body();

$windowMinutes = max(1, min(240, (int)($payload['window_minutes'] ?? 120)));
$devForce = (bool)($payload['dev_force_due'] ?? false);

$pdo = db();

try {
    $pdo->beginTransaction();

    $result = process_due_scheduled_services($pdo, $companyId, $windowMinutes, $devForce);

    $pdo->commit();

    json_response($result);
} catch (Throwable $exception) {
    if ($pdo->inTransaction()) {
        $pdo->rollBack();
    }

    json_response([
        'error' => 'PROCESS_DUE_SCHEDULED_SERVICES_FAILED',
        'message' => $exception->getMessage(),
    ], 500);
}
