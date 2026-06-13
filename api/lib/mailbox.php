<?php
declare(strict_types=1);

function mailbox_normalize_message_type(string $messageType): string
{
    $normalized = strtoupper(trim($messageType));

    $map = [
        'MISSED_SCHEDULED_FLIGHT' => 'DISPATCH_BLOCKED',
        'SCHEDULED_FLIGHT_MISSED' => 'DISPATCH_BLOCKED',
        'MAINTENANCE_COMPLETED' => 'MAINTENANCE_REQUIRED',
        'MAINTENANCE_STARTED' => 'MAINTENANCE_REQUIRED',
    ];

    if (isset($map[$normalized])) {
        return $map[$normalized];
    }

    $allowed = [
        'SYSTEM',
        'DISPATCH_BLOCKED',
        'MAINTENANCE_REQUIRED',
        'AIRCRAFT_FAULT_GROUND',
        'AIRCRAFT_FAULT_IN_FLIGHT',
        'FLIGHT_COMPLETED',
        'FINANCE',
        'STAFF',
    ];

    return in_array($normalized, $allowed, true) ? $normalized : 'SYSTEM';
}

function mailbox_normalize_severity(string $severity): string
{
    $normalized = strtoupper(trim($severity));
    return in_array($normalized, ['INFO', 'WARNING', 'CRITICAL'], true) ? $normalized : 'INFO';
}

function mailbox_send_company_message(
    PDO $pdo,
    int $companyId,
    string $messageType,
    string $severity,
    string $title,
    string $body,
    ?string $relatedEntityType = null,
    ?int $relatedEntityId = null
): void {
    $stmt = $pdo->prepare("
        INSERT INTO game_mailbox_messages (
          company_id,
          message_type,
          severity,
          status,
          title,
          body,
          related_entity_type,
          related_entity_id
        ) VALUES (
          :company_id,
          :message_type,
          :severity,
          'UNREAD',
          :title,
          :body,
          :related_entity_type,
          :related_entity_id
        )
    ");

    $stmt->execute([
        'company_id' => $companyId,
        'message_type' => mailbox_normalize_message_type($messageType),
        'severity' => mailbox_normalize_severity($severity),
        'title' => $title,
        'body' => $body,
        'related_entity_type' => $relatedEntityType,
        'related_entity_id' => $relatedEntityId,
    ]);
}
