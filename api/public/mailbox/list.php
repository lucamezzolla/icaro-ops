<?php
declare(strict_types=1);

require __DIR__ . '/../../lib/bootstrap.php';
require __DIR__ . '/../../lib/session.php';

$session = require_auth_session();
$companyId = $session['company_id'];

$status = strtoupper(trim((string)($_GET['status'] ?? '')));

$sql = "
    SELECT *
    FROM v_mailbox_messages
    WHERE company_id = :company_id
";

$params = ['company_id' => $companyId];

if ($status !== '') {
    if (!in_array($status, ['UNREAD', 'READ', 'RESOLVED', 'ARCHIVED'], true)) {
        json_response(['error' => 'INVALID_STATUS'], 422);
    }

    $sql .= " AND status = :status";
    $params['status'] = $status;
}

$sql .= " ORDER BY created_at_utc DESC LIMIT 200";

$stmt = db()->prepare($sql);
$stmt->execute($params);

json_response(array_map(static function (array $row): array {
    return [
        'message_id' => (int)$row['message_id'],
        'message_type' => $row['message_type'],
        'severity' => $row['severity'],
        'status' => $row['status'],
        'title' => $row['title'],
        'body' => $row['body'],
        'related_entity_type' => $row['related_entity_type'],
        'related_entity_id' => $row['related_entity_id'] !== null ? (int)$row['related_entity_id'] : null,
        'action_payload_json' => $row['action_payload_json'],
        'created_at_utc' => $row['created_at_utc'],
        'read_at_utc' => $row['read_at_utc'],
        'resolved_at_utc' => $row['resolved_at_utc'],
    ];
}, $stmt->fetchAll()));
