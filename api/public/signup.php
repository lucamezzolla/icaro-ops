<?php
declare(strict_types=1);

require __DIR__ . '/../lib/bootstrap.php';

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    json_response(['error' => 'METHOD_NOT_ALLOWED'], 405);
}

$payload = read_json_body();

$nickname = require_string($payload, 'nickname', 3, 40);
$companyName = require_string($payload, 'company_name', 3, 80);
$language = require_enum($payload, 'interface_language', ['it', 'en', 'es', 'pt', 'fr']);
$currency = require_enum($payload, 'currency_code', ['EUR', 'USD']);
$baseAirportIcao = strtoupper(require_string($payload, 'base_airport_icao_code', 4, 4));

$pdo = db();

try {
    $pdo->beginTransaction();

    $airportStmt = $pdo->prepare("
        SELECT
          icao_code,
          airport_name,
          country_name,
          world_region_name
        FROM v_starting_base_airports
        WHERE icao_code = :icao_code
        LIMIT 1
    ");
    $airportStmt->execute(['icao_code' => $baseAirportIcao]);
    $airport = $airportStmt->fetch();

    if (!$airport) {
        $pdo->rollBack();
        json_response([
            'error' => 'INVALID_STARTING_BASE',
            'message' => 'Selected airport is not available as a starting base.',
        ], 422);
    }

    $playerStmt = $pdo->prepare("
        INSERT INTO players (
          nickname,
          interface_language
        ) VALUES (
          :nickname,
          :interface_language
        )
    ");
    $playerStmt->execute([
        'nickname' => $nickname,
        'interface_language' => $language,
    ]);

    $playerId = (int)$pdo->lastInsertId();

    $companyStmt = $pdo->prepare("
        INSERT INTO companies (
          player_id,
          company_name,
          currency_code,
          base_airport_icao_code,
          budget_amount,
          reputation_score
        ) VALUES (
          :player_id,
          :company_name,
          :currency_code,
          :base_airport_icao_code,
          0.00,
          0
        )
    ");
    $companyStmt->execute([
        'player_id' => $playerId,
        'company_name' => $companyName,
        'currency_code' => $currency,
        'base_airport_icao_code' => $baseAirportIcao,
    ]);

    $companyId = (int)$pdo->lastInsertId();

    $stateStmt = $pdo->prepare("
        INSERT INTO company_market_offer_generation_state (
          company_id,
          last_generated_at_utc,
          next_generation_at_utc
        ) VALUES (
          :company_id,
          NULL,
          UTC_TIMESTAMP()
        )
    ");
    $stateStmt->execute(['company_id' => $companyId]);

    $pdo->commit();

    json_response([
        'player_id' => $playerId,
        'company_id' => $companyId,
        'nickname' => $nickname,
        'company_name' => $companyName,
        'currency_code' => $currency,
        'budget_amount' => '0.00',
        'base_airport' => $airport,
    ], 201);
} catch (PDOException $exception) {
    if ($pdo->inTransaction()) {
        $pdo->rollBack();
    }

    $sqlState = $exception->errorInfo[0] ?? '';
    $driverCode = $exception->errorInfo[1] ?? null;

    if ($sqlState === '23000' || $driverCode === 1062) {
        json_response([
            'error' => 'DUPLICATE_VALUE',
            'message' => 'Nickname or company name already exists.',
        ], 409);
    }

    json_response([
        'error' => 'DATABASE_ERROR',
        'message' => 'Unable to create company.',
    ], 500);
}
