<?php
declare(strict_types=1);

/*
 * Development-only account/company reset endpoint.
 *
 * WARNING:
 *   This endpoint deletes the currently logged-in player's game data,
 *   company, staff, aircraft, routes, flights, mailbox and user account.
 *
 * It must remain development-only.
 */

require __DIR__ . '/../../lib/bootstrap.php';
require __DIR__ . '/../../lib/session.php';

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    json_response(['error' => 'METHOD_NOT_ALLOWED'], 405);
}

/*
 * Basic local/dev guard.
 *
 * The PHP built-in server usually sets REMOTE_ADDR to 127.0.0.1.
 * This avoids exposing destructive reset on a public server by accident.
 */
$remoteAddr = $_SERVER['REMOTE_ADDR'] ?? '';
$host = $_SERVER['HTTP_HOST'] ?? '';

$isLocalRequest =
    in_array($remoteAddr, ['127.0.0.1', '::1'], true)
    || str_starts_with($host, '127.0.0.1:')
    || str_starts_with($host, 'localhost:');

if (!$isLocalRequest) {
    json_response([
        'error' => 'DEV_ONLY_ENDPOINT',
        'message' => 'This reset endpoint is only available from localhost.',
    ], 403);
}

$payload = read_json_body();
$confirm = (string)($payload['confirm'] ?? '');

if ($confirm !== 'RESET_MY_ICARO_OPS_DATA') {
    json_response([
        'error' => 'CONFIRMATION_REQUIRED',
        'message' => 'Send confirm=RESET_MY_ICARO_OPS_DATA to reset your development account.',
    ], 422);
}

$session = require_auth_session();

$playerId = (int)($session['player_id'] ?? 0);
$companyId = (int)($session['company_id'] ?? 0);

if ($playerId <= 0 || $companyId <= 0) {
    json_response([
        'error' => 'INVALID_SESSION',
        'message' => 'A logged-in player/company session is required.',
    ], 401);
}

$pdo = db();

try {
    $pdo->beginTransaction();

    /*
     * Lock the records first so we reset a stable account/company pair.
     */
    $companyStmt = $pdo->prepare("
        SELECT id, company_name
        FROM companies
        WHERE id = :company_id
          AND player_id = :player_id
        LIMIT 1
        FOR UPDATE
    ");
    $companyStmt->execute([
        'company_id' => $companyId,
        'player_id' => $playerId,
    ]);
    $company = $companyStmt->fetch();

    if (!$company) {
        $pdo->rollBack();
        json_response([
            'error' => 'COMPANY_NOT_FOUND',
            'message' => 'The logged-in company was not found or does not belong to the logged-in player.',
        ], 404);
    }

    /*
     * Delete child data explicitly.
     * Some tables have cascades, but explicit cleanup keeps the reset readable
     * and avoids surprises while schema is evolving.
     */

    delete_if_table_exists($pdo, 'route_dispatch_attempts', 'company_id', $companyId);
    delete_if_table_exists($pdo, 'reputation_journal', 'company_id', $companyId);

    delete_if_table_exists($pdo, 'aircraft_operational_events', 'company_id', $companyId);
    delete_if_table_exists($pdo, 'game_mailbox_messages', 'company_id', $companyId);

    delete_if_table_exists($pdo, 'scheduled_flight_instances', 'company_id', $companyId);
    delete_if_table_exists($pdo, 'company_routes', 'company_id', $companyId);

    /*
     * Staff licenses usually reference company_staff rows.
     */
    if (table_exists($pdo, 'company_staff_licenses') && table_exists($pdo, 'company_staff')) {
        $stmt = $pdo->prepare("
            DELETE l
            FROM company_staff_licenses l
            JOIN company_staff s
              ON s.id = l.company_staff_id
            WHERE s.company_id = :company_id
        ");
        $stmt->execute(['company_id' => $companyId]);
    }

    delete_if_table_exists($pdo, 'company_staff', 'company_id', $companyId);
    delete_if_table_exists($pdo, 'staff_candidates', 'company_id', $companyId);

    /*
     * Aircraft purchase offers can point to company aircraft and companies.
     */
    if (table_exists($pdo, 'aircraft_purchase_offers')) {
        $stmt = $pdo->prepare("
            DELETE apo
            FROM aircraft_purchase_offers apo
            LEFT JOIN company_aircraft ca
              ON ca.id = apo.aircraft_id
            WHERE apo.buyer_company_id = :company_id
               OR apo.seller_company_id = :company_id
               OR ca.company_id = :company_id
        ");
        $stmt->execute(['company_id' => $companyId]);
    }

    delete_if_table_exists($pdo, 'company_aircraft', 'company_id', $companyId);
    delete_if_table_exists($pdo, 'company_market_offer_generation_state', 'company_id', $companyId);

    /*
     * Finally remove company and player/user.
     */
    $deleteCompany = $pdo->prepare("
        DELETE FROM companies
        WHERE id = :company_id
          AND player_id = :player_id
    ");
    $deleteCompany->execute([
        'company_id' => $companyId,
        'player_id' => $playerId,
    ]);

    $deletePlayer = $pdo->prepare("
        DELETE FROM players
        WHERE id = :player_id
    ");
    $deletePlayer->execute(['player_id' => $playerId]);

    $pdo->commit();

    /*
     * Destroy PHP session so the browser is no longer logged in.
     */
    if (session_status() !== PHP_SESSION_ACTIVE) {
        session_start();
    }

    $_SESSION = [];

    if (ini_get('session.use_cookies')) {
        $params = session_get_cookie_params();
        setcookie(
            session_name(),
            '',
            time() - 42000,
            $params['path'],
            $params['domain'],
            (bool)$params['secure'],
            (bool)$params['httponly']
        );
    }

    session_destroy();

    json_response([
        'status' => 'RESET_COMPLETED',
        'deleted_player_id' => $playerId,
        'deleted_company_id' => $companyId,
        'deleted_company_name' => $company['company_name'],
        'next' => 'signup.html',
    ]);
} catch (Throwable $exception) {
    if ($pdo->inTransaction()) {
        $pdo->rollBack();
    }

    json_response([
        'error' => 'RESET_FAILED',
        'message' => 'Unable to reset development data.',
    ], 500);
}

function table_exists(PDO $pdo, string $tableName): bool
{
    $stmt = $pdo->prepare("
        SELECT COUNT(*)
        FROM information_schema.TABLES
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = :table_name
    ");
    $stmt->execute(['table_name' => $tableName]);

    return (int)$stmt->fetchColumn() > 0;
}

function delete_if_table_exists(PDO $pdo, string $tableName, string $companyColumnName, int $companyId): void
{
    if (!table_exists($pdo, $tableName)) {
        return;
    }

    /*
     * Table and column names are hardcoded by our own caller list above.
     * Do not pass user input here.
     */
    $sql = sprintf(
        'DELETE FROM `%s` WHERE `%s` = :company_id',
        str_replace('`', '``', $tableName),
        str_replace('`', '``', $companyColumnName)
    );

    $stmt = $pdo->prepare($sql);
    $stmt->execute(['company_id' => $companyId]);
}
