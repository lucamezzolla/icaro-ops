<?php
declare(strict_types=1);

/**
 * Aircraft purchase is budget-only, but aircraft operation still requires
 * realistic pilot type ratings.
 */
function required_aircraft_type_rating(PDO $pdo, string $modelCode): ?string
{
    $special = [
        'C208B_GRAND_CARAVAN_EX' => 'C208_TYPE',
        'DHC6_TWIN_OTTER_400' => 'DHC6_TYPE',
        'ATR42_600' => 'ATR42_TYPE',
    ];

    if (isset($special[$modelCode])) {
        return $special[$modelCode];
    }

    $stmt = $pdo->prepare("
        SELECT model_code, icao_type_code
        FROM aircraft_models
        WHERE model_code = :model_code
        LIMIT 1
    ");
    $stmt->execute(['model_code' => $modelCode]);
    $model = $stmt->fetch();

    if (!$model) {
        return null;
    }

    $icao = strtoupper(trim((string)($model['icao_type_code'] ?? '')));

    if ($icao !== '') {
        return $icao . '_TYPE';
    }

    $fallback = strtoupper(trim((string)($model['model_code'] ?? '')));

    if ($fallback !== '') {
        return preg_replace('/[^A-Z0-9_]/', '_', $fallback) . '_TYPE';
    }

    return null;
}
