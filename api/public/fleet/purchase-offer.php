<?php
declare(strict_types=1);

require __DIR__ . '/../../lib/bootstrap.php';

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    json_response(['error' => 'METHOD_NOT_ALLOWED'], 405);
}

$payload = read_json_body();

$aircraftId = (int)($payload['aircraft_id'] ?? 0);
$buyerCompanyId = (int)($payload['buyer_company_id'] ?? 0);
$offeredAmount = (float)($payload['offered_amount'] ?? 0);
$currencyCode = require_enum($payload, 'currency_code', ['EUR', 'USD']);

if ($aircraftId <= 0 || $buyerCompanyId <= 0 || $offeredAmount <= 0) {
    json_response(['error' => 'VALIDATION_ERROR', 'message' => 'aircraft_id, buyer_company_id and offered_amount are required.'], 422);
}

$pdo = db();

try {
    $pdo->beginTransaction();

    $listingStmt = $pdo->prepare("
        SELECT
          ca.id,
          ca.company_id AS seller_company_id,
          ca.is_available_for_sale,
          ca.status
        FROM company_aircraft ca
        WHERE ca.id = :aircraft_id
        LIMIT 1
    ");
    $listingStmt->execute(['aircraft_id' => $aircraftId]);
    $listing = $listingStmt->fetch();

    if (!$listing || !(bool)$listing['is_available_for_sale']) {
        $pdo->rollBack();
        json_response(['error' => 'AIRCRAFT_NOT_AVAILABLE', 'message' => 'Aircraft is not available on the used market.'], 404);
    }

    if ((int)$listing['seller_company_id'] === $buyerCompanyId) {
        $pdo->rollBack();
        json_response(['error' => 'INVALID_OFFER', 'message' => 'Buyer and seller cannot be the same company.'], 422);
    }

    $insertStmt = $pdo->prepare("
        INSERT INTO aircraft_purchase_offers (
          aircraft_id,
          buyer_company_id,
          seller_company_id,
          offered_amount,
          currency_code,
          status,
          expires_at_utc
        ) VALUES (
          :aircraft_id,
          :buyer_company_id,
          :seller_company_id,
          :offered_amount,
          :currency_code,
          'PENDING',
          DATE_ADD(UTC_TIMESTAMP(), INTERVAL 3 DAY)
        )
    ");
    $insertStmt->execute([
        'aircraft_id' => $aircraftId,
        'buyer_company_id' => $buyerCompanyId,
        'seller_company_id' => (int)$listing['seller_company_id'],
        'offered_amount' => $offeredAmount,
        'currency_code' => $currencyCode,
    ]);

    $offerId = (int)$pdo->lastInsertId();
    $pdo->commit();

    json_response([
        'aircraft_purchase_offer_id' => $offerId,
        'status' => 'PENDING',
    ], 201);
} catch (Throwable $exception) {
    if ($pdo->inTransaction()) {
        $pdo->rollBack();
    }

    json_response([
        'error' => 'DATABASE_ERROR',
        'message' => 'Unable to create purchase offer.',
    ], 500);
}
