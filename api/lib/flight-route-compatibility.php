<?php
declare(strict_types=1);

function determine_route_category_code(PDO $pdo, string $originIcao, string $destinationIcao, string $requestedType = 'ON_DEMAND'): string
{
    $requestedType = strtoupper(trim($requestedType));

    $specialMap = [
        'CHARTER' => 'CHT',
        'CARGO' => 'CGO',
        'HELICOPTER' => 'HEL',
        'MILITARY' => 'MIL',
        'RESCUE' => 'RES',
        'TRAINING' => 'TRN',
        'POSITIONING' => 'POS',
        'FERRY' => 'POS',
    ];

    if (isset($specialMap[$requestedType])) {
        return $specialMap[$requestedType];
    }

    $stmt = $pdo->prepare("
        SELECT
          oa.country_id AS origin_country_id,
          da.country_id AS destination_country_id
        FROM airports oa
        JOIN airports da ON da.icao_code = :destination
        WHERE oa.icao_code = :origin
        LIMIT 1
    ");
    $stmt->execute([
        'origin' => $originIcao,
        'destination' => $destinationIcao,
    ]);

    $row = $stmt->fetch();

    if ($row && $row['origin_country_id'] !== null && $row['destination_country_id'] !== null) {
        return ((string)$row['origin_country_id'] === (string)$row['destination_country_id']) ? 'DOM' : 'INT';
    }

    return 'DOM';
}

function route_scope_from_category(string $categoryCode): string
{
    return match (strtoupper($categoryCode)) {
        'INT' => 'INTERNATIONAL',
        'HEL' => 'HELICOPTER',
        'CGO' => 'CARGO',
        'MIL' => 'MILITARY',
        'RES' => 'RESCUE',
        'TRN' => 'TRAINING',
        'POS' => 'POSITIONING',
        'CHT' => 'CHARTER',
        default => 'DOMESTIC',
    };
}

function route_market_from_category(string $categoryCode): string
{
    return match (strtoupper($categoryCode)) {
        'HEL' => 'HEL',
        'CGO' => 'CGO',
        'MIL' => 'MIL',
        'RES' => 'RES',
        'TRN' => 'TRN',
        'CHT' => 'CHT',
        default => 'PAX',
    };
}

function next_route_public_code(PDO $pdo, string $categoryCode): string
{
    $categoryCode = strtoupper($categoryCode);

    $stmt = $pdo->prepare("
        SELECT MAX(CAST(SUBSTRING(route_public_code, LENGTH(:prefix) + 2) AS UNSIGNED))
        FROM air_routes
        WHERE route_public_code LIKE :pattern
    ");
    $stmt->execute([
        'prefix' => $categoryCode,
        'pattern' => $categoryCode . '-%',
    ]);

    return sprintf('%s-%04d', $categoryCode, ((int)$stmt->fetchColumn()) + 1);
}

function compatible_aircraft_models_for_route(PDO $pdo, string $categoryCode, float $distanceKm, int $minPassengers = 1, int $maxPassengers = 19): array
{
    $categoryCode = strtoupper($categoryCode);

    $allowedModelCodes = match ($categoryCode) {
        'HEL', 'RES' => [],
        'CGO' => ['C208B_GRAND_CARAVAN_EX', 'DHC6_TWIN_OTTER_400', 'L410_NG'],
        'CHT' => ['C208B_GRAND_CARAVAN_EX', 'PC12_NGX', 'B350_KING_AIR_360'],
        'TRN' => ['C208B_GRAND_CARAVAN_EX', 'PC12_NGX'],
        default => ['C208B_GRAND_CARAVAN_EX', 'PC12_NGX', 'DHC6_TWIN_OTTER_400', 'L410_NG'],
    };

    if (!$allowedModelCodes) {
        return [];
    }

    $placeholders = implode(',', array_fill(0, count($allowedModelCodes), '?'));

    $sql = "
        SELECT
          id,
          model_code,
          icao_type_code,
          manufacturer,
          model_name,
          passenger_capacity_standard,
          range_km,
          cruise_speed_kmh
        FROM aircraft_models
        WHERE model_code IN ({$placeholders})
          AND range_km >= ?
          AND passenger_capacity_standard >= ?
          AND passenger_capacity_standard <= ?
        ORDER BY FIELD(model_code, {$placeholders})
    ";

    $params = array_merge($allowedModelCodes, [max(1.0, $distanceKm), $minPassengers, $maxPassengers], $allowedModelCodes);
    $stmt = $pdo->prepare($sql);
    $stmt->execute($params);

    return $stmt->fetchAll();
}

function compatible_model_codes_csv(array $models): string
{
    return implode(',', array_map(static fn (array $model): string => (string)$model['model_code'], $models));
}

function compatible_icao_codes_csv(array $models): string
{
    $codes = [];
    foreach ($models as $model) {
        if (!empty($model['icao_type_code'])) {
            $codes[] = (string)$model['icao_type_code'];
        }
    }
    return implode(', ', array_values(array_unique($codes)));
}
