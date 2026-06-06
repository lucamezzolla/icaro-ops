<?php
declare(strict_types=1);

require_once __DIR__ . '/mailbox.php';

/*
 * Temporary balancing values.
 * TODO future damages/reputation design:
 * - replace fixed 100,000 penalty with damage/disruption model
 * - calculate passenger compensation
 * - scale reputation loss by route importance, frequency, delay history and company size
 */
const ICARO_MISSED_SCHEDULED_FLIGHT_PENALTY_AMOUNT = 100000.00;
const ICARO_MISSED_SCHEDULED_FLIGHT_REPUTATION_LOSS = 10;

function apply_missed_scheduled_flight_penalty(
    PDO $pdo,
    int $companyId,
    array $service,
    string $reason
): void {
    $companyStmt = $pdo->prepare("
        SELECT
          company_name,
          currency_code,
          budget_amount,
          reputation_score
        FROM companies
        WHERE id = :company_id
        LIMIT 1
        FOR UPDATE
    ");
    $companyStmt->execute(['company_id' => $companyId]);
    $company = $companyStmt->fetch();

    if (!$company) {
        throw new RuntimeException('Company not found while applying missed scheduled flight penalty.');
    }

    $currency = (string)($company['currency_code'] ?? 'EUR');
    $penalty = ICARO_MISSED_SCHEDULED_FLIGHT_PENALTY_AMOUNT;
    $reputationLoss = ICARO_MISSED_SCHEDULED_FLIGHT_REPUTATION_LOSS;

    $update = $pdo->prepare("
        UPDATE companies
        SET
          budget_amount = budget_amount - :penalty,
          reputation_score = GREATEST(0, reputation_score - :reputation_loss)
        WHERE id = :company_id
    ");
    $update->execute([
        'penalty' => number_format($penalty, 2, '.', ''),
        'reputation_loss' => $reputationLoss,
        'company_id' => $companyId,
    ]);

    $financial = $pdo->prepare("
        INSERT INTO company_financial_events (
          company_id,
          event_type,
          amount,
          currency_code,
          description,
          related_entity_type,
          related_entity_id
        ) VALUES (
          :company_id,
          'MISSED_SCHEDULED_FLIGHT_PENALTY',
          :amount,
          :currency_code,
          :description,
          'SCHEDULED_SERVICE',
          :related_entity_id
        )
    ");
    $financial->execute([
        'company_id' => $companyId,
        'amount' => number_format(-$penalty, 2, '.', ''),
        'currency_code' => $currency,
        'description' => $reason,
        'related_entity_id' => (int)$service['service_id'],
    ]);

    $flightCode = $service['flight_route_code'] ?: $service['service_code'];
    $origin = (string)$service['origin_airport_icao_code'];
    $destination = (string)$service['destination_airport_icao_code'];

    mailbox_send_company_message(
        $pdo,
        $companyId,
        'MISSED_SCHEDULED_FLIGHT',
        'CRITICAL',
        'Scheduled flight missed',
        sprintf(
            "Scheduled flight %s (%s → %s) could not depart because no compatible available aircraft was found at the origin airport. A temporary operational penalty of %s %s has been applied and reputation decreased by %d points. Reason: %s",
            $flightCode,
            $origin,
            $destination,
            number_format($penalty, 2, '.', ''),
            $currency,
            $reputationLoss,
            $reason
        ),
        'SCHEDULED_SERVICE',
        (int)$service['service_id']
    );
}
