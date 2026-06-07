<?php
declare(strict_types=1);

function remember_login_if_requested(?array $payload = null): void
{
    $remember = false;

    if (is_array($payload)) {
        $remember = filter_var($payload['remember_me'] ?? false, FILTER_VALIDATE_BOOLEAN);
    }

    if (!$remember && isset($_POST['remember_me'])) {
        $remember = filter_var($_POST['remember_me'], FILTER_VALIDATE_BOOLEAN);
    }

    if (!$remember) {
        setcookie('icaro_remember_me', '', [
            'expires' => time() - 42000,
            'path' => '/',
            'secure' => is_https_request(),
            'httponly' => true,
            'samesite' => 'Lax',
        ]);
        return;
    }

    if (session_status() !== PHP_SESSION_ACTIVE) {
        session_start();
    }

    $lifetime = 60 * 60 * 24 * 30;

    setcookie(session_name(), session_id(), [
        'expires' => time() + $lifetime,
        'path' => '/',
        'secure' => is_https_request(),
        'httponly' => true,
        'samesite' => 'Lax',
    ]);

    setcookie('icaro_remember_me', '1', [
        'expires' => time() + $lifetime,
        'path' => '/',
        'secure' => is_https_request(),
        'httponly' => true,
        'samesite' => 'Lax',
    ]);
}

function is_https_request(): bool
{
    return !empty($_SERVER['HTTPS']) && $_SERVER['HTTPS'] !== 'off';
}
