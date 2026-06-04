<?php
declare(strict_types=1);

require __DIR__ . '/../../lib/bootstrap.php';
require __DIR__ . '/../../lib/session.php';

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    json_response(['error' => 'METHOD_NOT_ALLOWED'], 405);
}

$payload = read_json_body();

$email = strtolower(trim((string)($payload['email'] ?? '')));
$password = (string)($payload['password'] ?? '');

if (!filter_var($email, FILTER_VALIDATE_EMAIL) || strlen($password) < 1) {
    json_response(['error' => 'INVALID_CREDENTIALS'], 401);
}

$stmt = db()->prepare("
    SELECT
      p.id AS player_id,
      p.first_name,
      p.last_name,
      p.email,
      p.password_hash,
      co.id AS company_id,
      co.company_name
    FROM players p
    JOIN companies co
      ON co.player_id = p.id
    WHERE p.email = :email
    ORDER BY co.id
    LIMIT 1
");

$stmt->execute(['email' => $email]);
$row = $stmt->fetch();

if (!$row || !is_string($row['password_hash']) || !password_verify($password, $row['password_hash'])) {
    json_response(['error' => 'INVALID_CREDENTIALS'], 401);
}

start_app_session();
session_regenerate_id(true);

$_SESSION['player_id'] = (int)$row['player_id'];
$_SESSION['company_id'] = (int)$row['company_id'];

$update = db()->prepare("UPDATE players SET last_login_at_utc = UTC_TIMESTAMP() WHERE id = :player_id");
$update->execute(['player_id' => (int)$row['player_id']]);

json_response([
    'player_id' => (int)$row['player_id'],
    'company_id' => (int)$row['company_id'],
    'owner_name' => trim((string)$row['first_name'] . ' ' . (string)$row['last_name']),
    'email' => $row['email'],
    'company_name' => $row['company_name'],
]);
