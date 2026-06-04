<?php
declare(strict_types=1);

require __DIR__ . '/../lib/bootstrap.php';

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    json_response(['error' => 'METHOD_NOT_ALLOWED'], 405);
}

$payload = read_json_body();

$firstName = require_string($payload, 'first_name', 2, 60);
$lastName = require_string($payload, 'last_name', 2, 60);
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

    $capacityStmt = $pdo->prepare("
        SELECT
          COALESCE(acp.max_total_bases, 1) AS max_total_bases,
          (
            SELECT COUNT(*)
            FROM companies co
            WHERE co.base_airport_icao_code = :player_airport
          ) +
          (
            SELECT COUNT(*)
            FROM rival_company_bases rb
            WHERE rb.airport_icao_code = :rival_airport
          ) AS used_bases
        FROM airports a
        LEFT JOIN airport_capacity_profiles acp
          ON acp.airport_icao_code = a.icao_code
        WHERE a.icao_code = :airport
        LIMIT 1
    ");
    $capacityStmt->execute([
        'player_airport' => $baseAirportIcao,
        'rival_airport' => $baseAirportIcao,
        'airport' => $baseAirportIcao,
    ]);
    $capacity = $capacityStmt->fetch();

    if ($capacity && (int)$capacity['used_bases'] >= (int)$capacity['max_total_bases']) {
        $pdo->rollBack();
        json_response([
            'error' => 'AIRPORT_BASE_CAPACITY_FULL',
            'message' => 'This airport has no free base slots.',
        ], 409);
    }

    $nickname = trim($firstName . ' ' . $lastName);

    $playerStmt = $pdo->prepare("
        INSERT INTO players (
          first_name,
          last_name,
          nickname,
          interface_language
        ) VALUES (
          :first_name,
          :last_name,
          :nickname,
          :interface_language
        )
    ");
    $playerStmt->execute([
        'first_name' => $firstName,
        'last_name' => $lastName,
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
        'owner_name' => $nickname,
        'first_name' => $firstName,
        'last_name' => $lastName,
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
            'message' => 'Owner name or company name already exists.',
        ], 409);
    }

    json_response([
        'error' => 'DATABASE_ERROR',
        'message' => 'Unable to create company.',
    ], 500);
}
