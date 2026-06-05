<?php
declare(strict_types=1);

require __DIR__ . '/../../lib/bootstrap.php';
require __DIR__ . '/../../lib/session.php';

$session = require_auth_session();
$companyId = (int)$session['company_id'];
$modelId = filter_input(INPUT_GET, 'modelId', FILTER_VALIDATE_INT);

if (!$modelId) {
    json_response(['error' => 'INVALID_MODEL_ID'], 422);
}

$pdo = db();

$companyStmt = $pdo->prepare("
    SELECT
      currency_code,
      base_airport_icao_code
    FROM companies
    WHERE id = :company_id
    LIMIT 1
");
$companyStmt->execute(['company_id' => $companyId]);
$company = $companyStmt->fetch() ?: [
    'currency_code' => 'EUR',
    'base_airport_icao_code' => null,
];

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

if ($priceColumn === null) {
    json_response(['error' => 'AIRCRAFT_PRICE_COLUMN_NOT_FOUND'], 500);
}

$optionalColumns = table_columns($pdo, 'aircraft_models');
$selectOptional = [];
foreach ([
    'cargo_capacity_kg',
    'runway_requirement_m',
    'service_ceiling_ft',
    'engine_type',
    'crew_required',
] as $column) {
    if (isset($optionalColumns[$column])) {
        $selectOptional[] = "`{$column}`";
    } else {
        $selectOptional[] = "NULL AS `{$column}`";
    }
}

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
      {$priceColumn} AS new_purchase_price,
      " . implode(",
      ", $selectOptional) . "
    FROM aircraft_models
    WHERE id = :model_id
    LIMIT 1
");
$stmt->execute(['model_id' => $modelId]);
$model = $stmt->fetch();

if (!$model) {
    json_response(['error' => 'AIRCRAFT_MODEL_NOT_FOUND'], 404);
}

$isConcorde = strtoupper((string)$model['model_code']) === 'CONCORDE';
$isStarterAllowed = in_array($model['model_code'], ['C208B_GRAND_CARAVAN_EX'], true);

$model['currency_code'] = $company['currency_code'] ?? 'EUR';
$model['is_available_for_current_level'] = (!$isConcorde && $isStarterAllowed);
$model['unlock_note'] = $model['is_available_for_current_level']
    ? 'Available for your current early-game operating level.'
    : 'Locked for your current level. It will be available later as your airline grows.';

json_response([
    'level' => [
        'base_airport_icao_code' => $company['base_airport_icao_code'] ?? null,
        'base_tier' => 'EARLY_GAME',
        'airport_size_tier' => null,
        'max_initial_aircraft_class' => 'LIGHT_COMMERCIAL',
    ],
    'model' => $model,
]);

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
