<?php
declare(strict_types=1);

require __DIR__ . '/../../lib/bootstrap.php';
require __DIR__ . '/../../lib/session.php';

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    json_response(['error' => 'METHOD_NOT_ALLOWED'], 405);
}

$session = require_auth_session();

$playerId = (int)$session['player_id'];
$companyId = (int)$session['company_id'];

$payload = read_json_body();
$confirmation = (string)($payload['confirmation'] ?? '');

if ($confirmation !== 'RESET_MY_ICARO_OPS_DATA') {
    json_response([
        'error' => 'INVALID_CONFIRMATION',
        'message' => 'Type RESET_MY_ICARO_OPS_DATA to confirm development reset.',
    ], 422);
}

$pdo = db();

try {
    $pdo->beginTransaction();

    delete_if_table_exists($pdo, 'flight_dispatch_requirements', 'scheduled_flight_instance_id IN (SELECT id FROM scheduled_flight_instances WHERE company_id = ?)', [$companyId]);
    delete_if_table_exists($pdo, 'aircraft_operational_events', 'company_id = ?', [$companyId]);
    delete_if_table_exists($pdo, 'game_mailbox_messages', 'company_id = ?', [$companyId]);
    delete_if_table_exists($pdo, 'maintenance_jobs', 'company_id = ?', [$companyId]);
    delete_if_table_exists($pdo, 'aircraft_maintenance_events', 'company_id = ?', [$companyId]);
    delete_if_table_exists($pdo, 'reputation_journal', 'company_id = ?', [$companyId]);
    delete_if_table_exists($pdo, 'scheduled_flight_instances', 'company_id = ?', [$companyId]);
    delete_if_table_exists($pdo, 'scheduled_services', 'company_id = ?', [$companyId]);
    delete_if_table_exists($pdo, 'aircraft_purchase_offers', 'buyer_company_id = ? OR seller_company_id = ?', [$companyId, $companyId]);
    delete_if_table_exists($pdo, 'company_routes', 'company_id = ?', [$companyId]);
    delete_if_table_exists($pdo, 'company_aircraft', 'company_id = ?', [$companyId]);

    if (table_exists($pdo, 'company_staff_licenses') && table_exists($pdo, 'company_staff')) {
        $stmt = $pdo->prepare("
            DELETE l
            FROM company_staff_licenses l
            JOIN company_staff s
              ON s.id = l.company_staff_id
            WHERE s.company_id = ?
        ");
        $stmt->execute([$companyId]);
    }

    delete_if_table_exists($pdo, 'company_staff', 'company_id = ?', [$companyId]);

    /*
     * In development reset we clean the candidate market too,
     * so signup/restart can generate a fresh pool.
     */
    delete_if_table_exists($pdo, 'staff_candidate_licenses', '1 = 1', []);
    delete_if_table_exists($pdo, 'staff_candidates', '1 = 1', []);

    delete_if_table_exists($pdo, 'companies', 'id = ?', [$companyId]);
    delete_if_table_exists($pdo, 'players', 'id = ?', [$playerId]);

    $pdo->commit();

    destroy_current_session_cookie();

    json_response([
        'status' => 'RESET_DONE',
        'logout' => true,
        'redirect_to' => 'signup.html',
        'message' => 'Development account reset completed. Session destroyed.',
    ]);
} catch (Throwable $exception) {
    if ($pdo->inTransaction()) {
        $pdo->rollBack();
    }

    json_response([
        'error' => 'RESET_FAILED',
        'message' => 'Development reset failed.',
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

function delete_if_table_exists(PDO $pdo, string $tableName, string $whereSql, array $params): void
{
    if (!table_exists($pdo, $tableName)) {
        return;
    }

    $stmt = $pdo->prepare("DELETE FROM {$tableName} WHERE {$whereSql}");
    $stmt->execute($params);
}

function destroy_current_session_cookie(): void
{
    if (session_status() !== PHP_SESSION_ACTIVE) {
        session_start();
    }

    $_SESSION = [];

    $params = session_get_cookie_params();

    setcookie(
        session_name(),
        '',
        [
            'expires' => time() - 42000,
            'path' => $params['path'] ?: '/',
            'domain' => $params['domain'] ?: '',
            'secure' => (bool)$params['secure'],
            'httponly' => (bool)$params['httponly'],
            'samesite' => $params['samesite'] ?? 'Lax',
        ]
    );

    session_destroy();
}
