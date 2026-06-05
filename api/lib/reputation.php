<?php
declare(strict_types=1);

function apply_reputation_event(
    PDO $pdo,
    int $companyId,
    string $eventCode,
    ?string $relatedEntityType,
    ?int $relatedEntityId,
    string $reason
): array {
    $ruleStmt = $pdo->prepare("
        SELECT reputation_delta, min_reputation, max_reputation, is_active
        FROM reputation_rules
        WHERE event_code = :event_code
        LIMIT 1
    ");
    $ruleStmt->execute(['event_code' => $eventCode]);
    $rule = $ruleStmt->fetch();

    if (!$rule || !(bool)$rule['is_active']) {
        return ['applied' => false, 'event_code' => $eventCode];
    }

    $companyStmt = $pdo->prepare("
        SELECT reputation_score
        FROM companies
        WHERE id = :company_id
        LIMIT 1
        FOR UPDATE
    ");
    $companyStmt->execute(['company_id' => $companyId]);
    $before = $companyStmt->fetchColumn();

    if ($before === false) {
        return ['applied' => false, 'event_code' => $eventCode];
    }

    $before = (int)$before;
    $delta = (int)$rule['reputation_delta'];
    $after = max((int)$rule['min_reputation'], min((int)$rule['max_reputation'], $before + $delta));

    if ($after !== $before) {
        $pdo->prepare("
            UPDATE companies
            SET reputation_score = :score
            WHERE id = :company_id
        ")->execute([
            'score' => $after,
            'company_id' => $companyId,
        ]);
    }

    $pdo->prepare("
        INSERT INTO reputation_journal (
          company_id,
          event_code,
          reputation_before,
          reputation_delta,
          reputation_after,
          related_entity_type,
          related_entity_id,
          reason
        ) VALUES (
          :company_id,
          :event_code,
          :before_score,
          :delta_score,
          :after_score,
          :related_entity_type,
          :related_entity_id,
          :reason
        )
    ")->execute([
        'company_id' => $companyId,
        'event_code' => $eventCode,
        'before_score' => $before,
        'delta_score' => $delta,
        'after_score' => $after,
        'related_entity_type' => $relatedEntityType,
        'related_entity_id' => $relatedEntityId,
        'reason' => $reason,
    ]);

    return [
        'applied' => true,
        'event_code' => $eventCode,
        'reputation_before' => $before,
        'reputation_delta' => $delta,
        'reputation_after' => $after,
        'journal_id' => (int)$pdo->lastInsertId(),
    ];
}
