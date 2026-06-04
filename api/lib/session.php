<?php
declare(strict_types=1);

function start_app_session(): void
{
    if (session_status() === PHP_SESSION_ACTIVE) {
        return;
    }

    session_set_cookie_params([
        'lifetime' => 60 * 60 * 24 * 30,
        'path' => '/',
        'httponly' => true,
        'samesite' => 'Lax',
        // Keep false for local http://127.0.0.1 development.
        // Set true behind HTTPS in production.
        'secure' => false,
    ]);

    session_start();
}

function require_auth_session(): array
{
    start_app_session();

    $playerId = $_SESSION['player_id'] ?? null;
    $companyId = $_SESSION['company_id'] ?? null;

    if (!$playerId || !$companyId) {
        json_response(['error' => 'UNAUTHENTICATED'], 401);
    }

    return [
        'player_id' => (int)$playerId,
        'company_id' => (int)$companyId,
    ];
}
