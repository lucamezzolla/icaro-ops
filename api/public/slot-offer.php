<?php
declare(strict_types=1);

require __DIR__ . '/../lib/bootstrap.php';

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    json_response(['error' => 'METHOD_NOT_ALLOWED'], 405);
}

$payload = read_json_body();

$airportIcao = strtoupper(require_string($payload, 'airport_icao_code', 4, 4));
$requesterCompanyId = (int)($payload['requester_company_id'] ?? 0);
$offeredAmount = (float)($payload['offered_amount'] ?? 0);
$currencyCode = require_enum($payload, 'currency_code', ['EUR', 'USD']);

if ($requesterCompanyId <= 0) {
    json_response([
        'error' => 'VALIDATION_ERROR',
        'field' => 'requester_company_id',
        'message' => 'requester_company_id is required.',
    ], 422);
}

if ($offeredAmount <= 0) {
    json_response([
        'error' => 'VALIDATION_ERROR',
        'field' => 'offered_amount',
        'message' => 'offered_amount must be greater than zero.',
    ], 422);
}

$pdo = db();

try {
    $pdo->beginTransaction();

    $capacityStmt = $pdo->prepare("
        SELECT
          airport_icao_code,
          is_full,
          available_total_base_slots
        FROM v_airport_base_capacity_status
        WHERE airport_icao_code = :airport
        LIMIT 1
    ");
    $capacityStmt->execute(['airport' => $airportIcao]);
    $capacity = $capacityStmt->fetch();

    if (!$capacity) {
        $pdo->rollBack();
        json_response(['error' => 'AIRPORT_NOT_FOUND'], 404);
    }

    $companyStmt = $pdo->prepare("
        SELECT id
        FROM companies
        WHERE id = :company_id
        LIMIT 1
    ");
    $companyStmt->execute(['company_id' => $requesterCompanyId]);

    if (!$companyStmt->fetch()) {
        $pdo->rollBack();
        json_response(['error' => 'COMPANY_NOT_FOUND'], 404);
    }

    $offerStmt = $pdo->prepare("
        INSERT INTO airport_base_slot_offers (
          airport_icao_code,
          requester_type,
          requester_company_id,
          offered_amount,
          currency_code,
          status
        ) VALUES (
          :airport_icao_code,
          'PLAYER',
          :requester_company_id,
          :offered_amount,
          :currency_code,
          'PENDING'
        )
    ");

    $offerStmt->execute([
        'airport_icao_code' => $airportIcao,
        'requester_company_id' => $requesterCompanyId,
        'offered_amount' => $offeredAmount,
        'currency_code' => $currencyCode,
    ]);

    $offerId = (int)$pdo->lastInsertId();

    $pdo->commit();

    json_response([
        'slot_offer_id' => $offerId,
        'airport_icao_code' => $airportIcao,
        'requester_company_id' => $requesterCompanyId,
        'offered_amount' => number_format($offeredAmount, 2, '.', ''),
        'currency_code' => $currencyCode,
        'status' => 'PENDING',
        'airport_is_full' => (bool)$capacity['is_full'],
        'available_total_base_slots' => (int)$capacity['available_total_base_slots'],
    ], 201);
} catch (PDOException $exception) {
    if ($pdo->inTransaction()) {
        $pdo->rollBack();
    }

    json_response([
        'error' => 'DATABASE_ERROR',
        'message' => 'Unable to create slot offer.',
    ], 500);
}
