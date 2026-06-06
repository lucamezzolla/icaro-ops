<?php
declare(strict_types=1);

require __DIR__ . '/../../lib/bootstrap.php';
require __DIR__ . '/../../lib/session.php';

require_auth_session();

$icao = strtoupper(trim((string)($_GET['icao'] ?? $_GET['icao_type_code'] ?? '')));

if (!preg_match('/^[A-Z0-9]{2,4}$/', $icao)) {
    json_response(['error' => 'INVALID_ICAO_TYPE_CODE'], 422);
}

$pdo = db();

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
      {$priceExpr}
    FROM aircraft_models
    WHERE icao_type_code = :icao
    ORDER BY manufacturer, model_name
    LIMIT 1
");
$stmt->execute(['icao' => $icao]);

$model = $stmt->fetch();

if (!$model) {
    json_response(['error' => 'AIRCRAFT_MODEL_NOT_FOUND'], 404);
}

json_response(['model' => $model]);

function table_columns(PDO $pdo, string $tableName): array
{
    $stmt = $pdo->prepare("
        SELECT COLUMN_NAME
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = :table_name
    ");
    $stmt->execute(['table_name' => $tableName]);
    return array_flip(array_map(static fn ($row) => $row['COLUMN_NAME'], $stmt->fetchAll()));
}

function first_existing_column(PDO $pdo, string $tableName, array $candidates): ?string
{
    $columns = table_columns($pdo, $tableName);
    foreach ($candidates as $candidate) {
        if (isset($columns[$candidate])) {
            return '`' . str_replace('`', '``', $candidate) . '`';
        }
    }
    return null;
}
