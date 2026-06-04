<?php
declare(strict_types=1);

function load_config(): array
{
    $local = __DIR__ . '/../config.local.php';
    $example = __DIR__ . '/../config.example.php';

    if (is_file($local)) {
        return require $local;
    }

    return require $example;
}

function db(): PDO
{
    static $pdo = null;

    if ($pdo instanceof PDO) {
        return $pdo;
    }

    $config = load_config();
    $db = $config['db'];

    $dsn = sprintf(
        'mysql:host=%s;port=%d;dbname=%s;charset=%s',
        $db['host'],
        $db['port'],
        $db['database'],
        $db['charset']
    );

    $pdo = new PDO(
        $dsn,
        $db['username'],
        $db['password'],
        [
            PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
            PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
            PDO::ATTR_EMULATE_PREPARES => false,
        ]
    );

    return $pdo;
}

function json_response(array $payload, int $status = 200): void
{
    http_response_code($status);
    header('Content-Type: application/json; charset=utf-8');
    echo json_encode($payload, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
    exit;
}

function read_json_body(): array
{
    $raw = file_get_contents('php://input');

    if ($raw === false || trim($raw) === '') {
        return [];
    }

    $decoded = json_decode($raw, true);

    if (!is_array($decoded)) {
        json_response(['error' => 'INVALID_JSON'], 400);
    }

    return $decoded;
}

function require_string(array $payload, string $key, int $minLength, int $maxLength): string
{
    $value = trim((string)($payload[$key] ?? ''));

    if (mb_strlen($value) < $minLength || mb_strlen($value) > $maxLength) {
        json_response([
            'error' => 'VALIDATION_ERROR',
            'field' => $key,
            'message' => sprintf('%s must be between %d and %d characters.', $key, $minLength, $maxLength),
        ], 422);
    }

    return $value;
}

function require_enum(array $payload, string $key, array $allowed): string
{
    $value = trim((string)($payload[$key] ?? ''));

    if (!in_array($value, $allowed, true)) {
        json_response([
            'error' => 'VALIDATION_ERROR',
            'field' => $key,
            'message' => sprintf('%s has an invalid value.', $key),
        ], 422);
    }

    return $value;
}
