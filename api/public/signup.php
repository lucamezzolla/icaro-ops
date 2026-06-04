<?php
declare(strict_types=1);

require __DIR__ . '/../lib/bootstrap.php';
require __DIR__ . '/../lib/session.php';

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    json_response(['error' => 'METHOD_NOT_ALLOWED'], 405);
}

$payload = read_json_body();

$firstName = trim(require_string($payload, 'first_name', 2, 80));
$lastName = trim(require_string($payload, 'last_name', 2, 80));
$email = strtolower(trim(require_string($payload, 'email', 5, 190)));
$password = (string)($payload['password'] ?? '');
$companyName = trim(require_string($payload, 'company_name', 2, 120));
$interfaceLanguage = require_enum($payload, 'interface_language', ['it', 'en', 'es', 'pt', 'fr']);
$currencyCode = require_enum($payload, 'currency_code', ['EUR', 'USD']);
$baseAirportIcao = strtoupper(trim(require_string($payload, 'base_airport_icao_code', 4, 4)));

if (!filter_var($email, FILTER_VALIDATE_EMAIL)) {
    json_response([
        'error' => 'VALIDATION_ERROR',
        'field' => 'email',
        'message' => 'A valid email is required.',
    ], 422);
}

if (strlen($password) < 8) {
    json_response([
        'error' => 'VALIDATION_ERROR',
        'field' => 'password',
        'message' => 'Password must be at least 8 characters.',
    ], 422);
}

$pdo = db();

try {
    $pdo->beginTransaction();

    $emailStmt = $pdo->prepare("SELECT id FROM players WHERE email = :email LIMIT 1");
    $emailStmt->execute(['email' => $email]);

    if ($emailStmt->fetch()) {
        $pdo->rollBack();
        json_response(['error' => 'EMAIL_ALREADY_REGISTERED'], 409);
    }

    $airportStmt = $pdo->prepare("
        SELECT
          a.icao_code,
          a.iata_code,
          a.name AS airport_name,
          c.name AS country_name,
          wr.name AS world_region_name,
          cap.max_total_bases,
          cap.used_total_bases,
          cap.available_total_base_slots,
          cap.is_full
        FROM airports a
        JOIN countries c
          ON c.id = a.country_id
        JOIN world_regions wr
          ON wr.code = c.world_region_code
        LEFT JOIN v_airport_base_capacity_status cap
          ON cap.airport_icao_code = a.icao_code
        WHERE a.icao_code = :icao
          AND a.is_closed = FALSE
          AND a.is_civilian = TRUE
        LIMIT 1
    ");
    $airportStmt->execute(['icao' => $baseAirportIcao]);
    $airport = $airportStmt->fetch();

    if (!$airport) {
        $pdo->rollBack();
        json_response(['error' => 'INVALID_BASE_AIRPORT'], 422);
    }

    if (isset($airport['is_full']) && (bool)$airport['is_full']) {
        $pdo->rollBack();
        json_response([
            'error' => 'AIRPORT_BASE_CAPACITY_FULL',
            'message' => 'This airport has no free base slots.',
            'can_create_slot_offer' => true,
        ], 409);
    }

    $settingsStmt = $pdo->prepare("SELECT setting_value FROM game_settings WHERE setting_key = 'initial_company_budget' LIMIT 1");
    $settingsStmt->execute();
    $initialBudget = (float)($settingsStmt->fetchColumn() ?: 7000000.00);

    $playerStmt = $pdo->prepare("
        INSERT INTO players (
          nickname,
          first_name,
          last_name,
          email,
          password_hash,
          interface_language
        ) VALUES (
          :nickname,
          :first_name,
          :last_name,
          :email,
          :password_hash,
          :interface_language
        )
    ");

    $nickname = strtolower(preg_replace('/[^a-z0-9]+/i', '', explode('@', $email)[0])) ?: 'pilot';

    $playerStmt->execute([
        'nickname' => $nickname,
        'first_name' => $firstName,
        'last_name' => $lastName,
        'email' => $email,
        'password_hash' => password_hash($password, PASSWORD_DEFAULT),
        'interface_language' => $interfaceLanguage,
    ]);

    $playerId = (int)$pdo->lastInsertId();

    $companyStmt = $pdo->prepare("
        INSERT INTO companies (
          player_id,
          company_name,
          currency_code,
          budget_amount,
          base_airport_icao_code,
          reputation_score
        ) VALUES (
          :player_id,
          :company_name,
          :currency_code,
          :budget_amount,
          :base_airport_icao_code,
          0
        )
    ");

    $companyStmt->execute([
        'player_id' => $playerId,
        'company_name' => $companyName,
        'currency_code' => $currencyCode,
        'budget_amount' => $initialBudget,
        'base_airport_icao_code' => $baseAirportIcao,
    ]);

    $companyId = (int)$pdo->lastInsertId();

    $pdo->commit();

    start_app_session();
    session_regenerate_id(true);
    $_SESSION['player_id'] = $playerId;
    $_SESSION['company_id'] = $companyId;

    json_response([
        'player_id' => $playerId,
        'company_id' => $companyId,
        'first_name' => $firstName,
        'last_name' => $lastName,
        'owner_name' => trim($firstName . ' ' . $lastName),
        'email' => $email,
        'company_name' => $companyName,
        'currency_code' => $currencyCode,
        'budget_amount' => number_format($initialBudget, 2, '.', ''),
        'base_airport' => [
            'icao_code' => $airport['icao_code'],
            'iata_code' => $airport['iata_code'],
            'airport_name' => $airport['airport_name'],
            'country_name' => $airport['country_name'],
            'world_region_name' => $airport['world_region_name'],
        ],
    ], 201);
} catch (PDOException $exception) {
    if ($pdo->inTransaction()) {
        $pdo->rollBack();
    }

    json_response([
        'error' => 'DATABASE_ERROR',
        'message' => 'Unable to create player/company.',
    ], 500);
}
