<?php
declare(strict_types=1);

require __DIR__ . '/../../lib/bootstrap.php';

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    json_response(['error' => 'METHOD_NOT_ALLOWED'], 405);
}

$payload = read_json_body();

$companyId = (int)($payload['company_id'] ?? 0);
$modelId = (int)($payload['aircraft_model_id'] ?? 0);

if ($companyId <= 0 || $modelId <= 0) {
    json_response(['error' => 'VALIDATION_ERROR', 'message' => 'company_id and aircraft_model_id are required.'], 422);
}

$pdo = db();

try {
    $pdo->beginTransaction();

    $companyStmt = $pdo->prepare("
        SELECT
          co.id,
          co.currency_code,
          co.budget_amount,
          co.reputation_score,
          co.base_airport_icao_code,
          bc.free_managed_aircraft_slots
        FROM companies co
        LEFT JOIN v_player_base_aircraft_capacity_status bc
          ON bc.company_id = co.id
         AND bc.airport_icao_code = co.base_airport_icao_code
        WHERE co.id = :company_id
        LIMIT 1
        FOR UPDATE
    ");
    $companyStmt->execute(['company_id' => $companyId]);
    $company = $companyStmt->fetch();

    if (!$company) {
        $pdo->rollBack();
        json_response(['error' => 'COMPANY_NOT_FOUND'], 404);
    }

    $modelStmt = $pdo->prepare("
        SELECT *
        FROM aircraft_models
        WHERE id = :model_id
        LIMIT 1
    ");
    $modelStmt->execute(['model_id' => $modelId]);
    $model = $modelStmt->fetch();

    if (!$model || !(bool)$model['is_active'] || !(bool)$model['is_available_new'] || (bool)$model['is_endgame']) {
        $pdo->rollBack();
        json_response(['error' => 'AIRCRAFT_MODEL_UNAVAILABLE', 'message' => 'Aircraft model is not available for new purchase.'], 422);
    }

    if ((int)$company['reputation_score'] < (int)$model['unlock_reputation_score']) {
        $pdo->rollBack();
        json_response(['error' => 'REPUTATION_LOCKED', 'message' => 'Company reputation is too low for this aircraft.'], 409);
    }

    if ((int)($company['free_managed_aircraft_slots'] ?? 0) <= 0) {
        $pdo->rollBack();
        json_response(['error' => 'NO_FLEET_SLOTS', 'message' => 'No free aircraft slots at this base.'], 409);
    }

    $price = (float)$model['new_purchase_price'];
    $budget = (float)$company['budget_amount'];

    if ($budget < $price) {
        $pdo->rollBack();
        json_response(['error' => 'INSUFFICIENT_FUNDS', 'message' => 'Company budget is not enough to buy this aircraft.'], 409);
    }

    $registration = generate_registration($pdo, $companyId);
    $serial = 'IO-' . strtoupper(bin2hex(random_bytes(4)));

    $insertStmt = $pdo->prepare("
        INSERT INTO company_aircraft (
          company_id,
          aircraft_model_id,
          registration_code,
          serial_number,
          manufacture_year,
          ownership_status,
          acquisition_type,
          purchase_price,
          current_market_value,
          currency_code,
          home_base_icao_code,
          current_airport_icao_code,
          condition_percent,
          airframe_hours,
          cycles_count,
          status,
          is_available_for_sale,
          asking_price
        ) VALUES (
          :company_id,
          :aircraft_model_id,
          :registration_code,
          :serial_number,
          YEAR(UTC_DATE()),
          'OWNED',
          'NEW_PURCHASE',
          :purchase_price,
          :current_market_value,
          :currency_code,
          :home_base_icao_code,
          :current_airport_icao_code,
          100.00,
          0.00,
          0,
          'AVAILABLE',
          FALSE,
          NULL
        )
    ");
    $insertStmt->execute([
        'company_id' => $companyId,
        'aircraft_model_id' => $modelId,
        'registration_code' => $registration,
        'serial_number' => $serial,
        'purchase_price' => $price,
        'current_market_value' => $price * 0.92,
        'currency_code' => $company['currency_code'],
        'home_base_icao_code' => $company['base_airport_icao_code'],
        'current_airport_icao_code' => $company['base_airport_icao_code'],
    ]);

    $aircraftId = (int)$pdo->lastInsertId();

    $budgetStmt = $pdo->prepare("
        UPDATE companies
        SET budget_amount = budget_amount - :price
        WHERE id = :company_id
    ");
    $budgetStmt->execute([
        'price' => $price,
        'company_id' => $companyId,
    ]);

    $pdo->commit();

    json_response([
        'company_aircraft_id' => $aircraftId,
        'registration_code' => $registration,
        'purchase_price' => number_format($price, 2, '.', ''),
    ], 201);
} catch (Throwable $exception) {
    if ($pdo->inTransaction()) {
        $pdo->rollBack();
    }

    json_response([
        'error' => 'DATABASE_ERROR',
        'message' => 'Unable to buy aircraft.',
    ], 500);
}

function generate_registration(PDO $pdo, int $companyId): string
{
    for ($i = 0; $i < 20; $i++) {
        $candidate = 'IO-' . str_pad((string)$companyId, 3, '0', STR_PAD_LEFT) . '-' . strtoupper(substr(bin2hex(random_bytes(2)), 0, 4));

        $stmt = $pdo->prepare("SELECT id FROM company_aircraft WHERE registration_code = :registration LIMIT 1");
        $stmt->execute(['registration' => $candidate]);

        if (!$stmt->fetch()) {
            return $candidate;
        }
    }

    return 'IO-' . str_pad((string)$companyId, 3, '0', STR_PAD_LEFT) . '-' . time();
}
