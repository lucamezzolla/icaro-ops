<?php
declare(strict_types=1);

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
        INSERT INTO company_mailbox_messages (
          company_id,
          message_type,
          severity,
          title,
          body,
          related_entity_type,
          related_entity_id
        ) VALUES (
          :company_id,
          :message_type,
          :severity,
          :title,
          :body,
          :related_entity_type,
          :related_entity_id
        )
    ");

    $stmt->execute([
        'company_id' => $companyId,
        'message_type' => $messageType,
        'severity' => $severity,
        'title' => $title,
        'body' => $body,
        'related_entity_type' => $relatedEntityType,
        'related_entity_id' => $relatedEntityId,
    ]);
}
