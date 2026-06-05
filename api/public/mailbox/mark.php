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

$messageId = (int)($payload['message_id'] ?? 0);
$action = strtoupper(trim((string)($payload['action'] ?? 'READ')));

if ($messageId <= 0) {
    json_response(['error' => 'VALIDATION_ERROR', 'message' => 'message_id is required.'], 422);
}

if (!in_array($action, ['READ', 'RESOLVE', 'ARCHIVE'], true)) {
    json_response(['error' => 'INVALID_ACTION'], 422);
}

$status = match ($action) {
    'READ' => 'READ',
    'RESOLVE' => 'RESOLVED',
    'ARCHIVE' => 'ARCHIVED',
};

$setSql = match ($action) {
    'READ' => "status = 'READ', read_at_utc = COALESCE(read_at_utc, UTC_TIMESTAMP())",
    'RESOLVE' => "status = 'RESOLVED', read_at_utc = COALESCE(read_at_utc, UTC_TIMESTAMP()), resolved_at_utc = UTC_TIMESTAMP()",
    'ARCHIVE' => "status = 'ARCHIVED'",
};

$stmt = db()->prepare("
    UPDATE game_mailbox_messages
    SET $setSql
    WHERE id = :message_id
      AND company_id = :company_id
");

$stmt->execute([
    'message_id' => $messageId,
    'company_id' => $companyId,
]);

if ($stmt->rowCount() === 0) {
    json_response(['error' => 'MESSAGE_NOT_FOUND'], 404);
}

json_response([
    'message_id' => $messageId,
    'status' => $status,
]);
