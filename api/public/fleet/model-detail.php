<?php
declare(strict_types=1);


function resolve_aircraft_model_id_from_request(PDO $pdo): int
{
    $id = isset($_GET['modelId']) ? (int)$_GET['modelId'] : (isset($_GET['id']) ? (int)$_GET['id'] : 0);

    if ($id > 0) {
        return $id;
    }

    $modelCode = trim((string)($_GET['model_code'] ?? $_GET['modelCode'] ?? ''));
    $icao = trim((string)($_GET['icao'] ?? $_GET['icao_type_code'] ?? $_GET['icaoTypeCode'] ?? ''));

    if ($modelCode !== '') {
        $stmt = $pdo->prepare('SELECT id FROM aircraft_models WHERE model_code = :model_code LIMIT 1');
        $stmt->execute(['model_code' => $modelCode]);
        $found = (int)($stmt->fetchColumn() ?: 0);

        if ($found > 0) {
            return $found;
        }
    }

    if ($icao !== '') {
        $stmt = $pdo->prepare('SELECT id FROM aircraft_models WHERE icao_type_code = :icao ORDER BY new_purchase_price ASC, id ASC LIMIT 1');
        $stmt->execute(['icao' => $icao]);
        $found = (int)($stmt->fetchColumn() ?: 0);

        if ($found > 0) {
            return $found;
        }
    }

    return 0;
}
require __DIR__ . '/../../lib/bootstrap.php';
require __DIR__ . '/../../lib/session.php';

require_auth_session();

$pdo = db();
$modelId = resolve_aircraft_model_id_from_request($pdo);

if ($modelId <= 0) {
    json_response(['error' => 'INVALID_MODEL_ID'], 422);
}

$priceColumn = first_existing_column($pdo, 'aircraft_models', [
    'new_purchase_price',
    'base_purchase_price',
    'new_price',
    'purchase_price',
    'estimated_new_price',
    'catalog_price',
    'price_amount',
    'new_cost_amount'
]);

$priceExpr = $priceColumn ? "{$priceColumn} AS new_purchase_price" : "NULL AS new_purchase_price";

$stmt = $pdo->prepare("
    SELECT
      id AS aircraft_model_id,
      id,
      manufacturer,
      model_name,
      model_code,
      icao_type_code,
      operation_role,
      passenger_capacity_standard,
      range_km,
      cruise_speed_kmh,
      fuel_burn_kg_per_hour,
      maintenance_cost_per_hour,
      image_asset_path,
      {$priceExpr},
      currency_code,
      is_active,
      is_available_new,
      is_endgame,
      unlock_reputation_score
    FROM aircraft_models
    WHERE id = :id
    LIMIT 1
");
$stmt->execute(['id' => $modelId]);

$model = $stmt->fetch();

if (!$model) {
    json_response(['error' => 'AIRCRAFT_MODEL_NOT_FOUND'], 404);
}

json_response(['model' => $model]);

function first_existing_column(PDO $pdo, string $tableName, array $candidates): ?string
{
    $stmt = $pdo->prepare("
        SELECT COLUMN_NAME
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = :table_name
    ");
    $stmt->execute(['table_name' => $tableName]);

    $columns = array_flip(array_map(static fn ($row) => $row['COLUMN_NAME'], $stmt->fetchAll()));

    foreach ($candidates as $candidate) {
        if (isset($columns[$candidate])) {
            return '`' . str_replace('`', '``', $candidate) . '`';
        }
    }

    return null;
}
