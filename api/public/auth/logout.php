<?php
declare(strict_types=1);

require __DIR__ . '/../../lib/bootstrap.php';

if (session_status() !== PHP_SESSION_ACTIVE) {
    session_start();
}

$_SESSION = [];
$params = session_get_cookie_params();

if (ini_get('session.use_cookies')) {
    setcookie(session_name(), '', [
        'expires' => time() - 42000,
        'path' => $params['path'] ?: '/',
        'domain' => $params['domain'] ?: '',
        'secure' => (bool)$params['secure'],
        'httponly' => (bool)$params['httponly'],
        'samesite' => $params['samesite'] ?: 'Lax',
    ]);
}

session_destroy();

setcookie('icaro_remember_me', '', [
    'expires' => time() - 42000,
    'path' => '/',
    'secure' => !empty($_SERVER['HTTPS']) && $_SERVER['HTTPS'] !== 'off',
    'httponly' => true,
    'samesite' => 'Lax',
]);

json_response(['status' => 'LOGGED_OUT']);
