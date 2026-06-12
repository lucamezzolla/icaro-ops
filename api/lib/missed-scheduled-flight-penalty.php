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

function missed_scheduled_flight_date_utc(array $service): string
{
    $scheduledDeparture = trim((string)($service['scheduled_departure_at_utc'] ?? ''));

    if ($scheduledDeparture !== '') {
        $timestamp = strtotime($scheduledDeparture . ' UTC');

        if ($timestamp !== false) {
            return gmdate('Y-m-d', $timestamp);
        }
    }

    return gmdate('Y-m-d');
}

function missed_scheduled_flight_penalty_already_applied(
    PDO $pdo,
    int $companyId,
    int $serviceId,
    string $flightDateUtc
): bool {
    $start = $flightDateUtc . ' 00:00:00';
    $end = gmdate('Y-m-d H:i:s', strtotime($start . ' UTC') + 86400);
    $dateMarker = '%Scheduled date: ' . $flightDateUtc . '%';

    $stmt = $pdo->prepare("
        SELECT COUNT(*)
        FROM company_financial_events
        WHERE company_id = :company_id
          AND event_type = 'MISSED_SCHEDULED_FLIGHT_PENALTY'
          AND related_entity_type = 'SCHEDULED_SERVICE'
          AND related_entity_id = :service_id
          AND (
            (created_at_utc >= :start_utc AND created_at_utc < :end_utc)
            OR description LIKE :date_marker
          )
    ");
    $stmt->execute([
        'company_id' => $companyId,
        'service_id' => $serviceId,
        'start_utc' => $start,
        'end_utc' => $end,
        'date_marker' => $dateMarker,
    ]);

    return (int)$stmt->fetchColumn() > 0;
}

function apply_missed_scheduled_flight_penalty(
    PDO $pdo,
    int $companyId,
    array $service,
    string $reason
): void {
    $serviceId = (int)($service['service_id'] ?? 0);
    $flightDateUtc = missed_scheduled_flight_date_utc($service);

    if ($serviceId > 0 && missed_scheduled_flight_penalty_already_applied($pdo, $companyId, $serviceId, $flightDateUtc)) {
        return;
    }

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
        'description' => sprintf('Scheduled date: %s. %s', $flightDateUtc, $reason),
        'related_entity_id' => $serviceId,
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
        $serviceId
    );
}
