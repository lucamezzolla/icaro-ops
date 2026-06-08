<?php
declare(strict_types=1);

require __DIR__ . '/../../lib/bootstrap.php';
require __DIR__ . '/../../lib/aircraft-images.php';
require __DIR__ . '/../../lib/session.php';

$session = require_auth_session();
$companyId = (int)$session['company_id'];
$pdo = db();

$companyStmt = $pdo->prepare("
    SELECT
      currency_code,
      base_airport_icao_code,
      budget_amount
    FROM companies
    WHERE id = :company_id
    LIMIT 1
");
$companyStmt->execute(['company_id' => $companyId]);
$company = $companyStmt->fetch() ?: [
    'currency_code' => 'EUR',
    'base_airport_icao_code' => null,
    'budget_amount' => 0,
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
    json_response([
        'error' => 'AIRCRAFT_PRICE_COLUMN_NOT_FOUND',
        'message' => 'No supported aircraft price column was found in aircraft_models.',
    ], 500);
}

$engineTypeColumn = first_existing_column($pdo, 'aircraft_models', [
    'engine_type'
]);
$engineTypeExpr = $engineTypeColumn !== null ? "COALESCE({$engineTypeColumn}, '')" : "''";

/*
 * Development/open market:
 * show every aircraft model. Purchase blocking is budget-only.
 */
$sql = "
    SELECT
      id AS aircraft_model_id,
      id,
      manufacturer,
      model_name,
      model_code,
      icao_type_code,
      {$engineTypeExpr} AS engine_type,
      operation_role,
      passenger_capacity_standard,
      range_km,
      cruise_speed_kmh,
      fuel_burn_kg_per_hour,
      maintenance_cost_per_hour,
      image_asset_path,
      COALESCE({$priceColumn}, 0) AS new_purchase_price,
      COALESCE(currency_code, :currency_code) AS currency_code,
      is_active,
      is_available_new,
      is_endgame,
      unlock_reputation_score
    FROM aircraft_models
    WHERE COALESCE(is_active, 1) = 1
    ORDER BY
      COALESCE({$priceColumn}, 0),
      manufacturer,
      model_name
";

$stmt = $pdo->prepare($sql);
$stmt->execute(['currency_code' => $company['currency_code'] ?? 'EUR']);

$aircraft = [];
$budget = (float)($company['budget_amount'] ?? 0);

foreach ($stmt->fetchAll() as $row) {
    $price = (float)($row['new_purchase_price'] ?? 0);

    $row['engine_type'] = strtoupper(trim((string)($row['engine_type'] ?? '')));
    $row['currency_code'] = $row['currency_code'] ?: ($company['currency_code'] ?? 'EUR');
    $row['purchase_rule'] = 'BUDGET_ONLY';
    $row['budget_amount'] = number_format($budget, 2, '.', '');
    $row['can_afford'] = $budget >= $price;

    /* Compatibility fields kept for the current UI, but they no longer block purchase. */
    $row['current_qualified_pilots'] = null;
    $row['required_pilots_after_purchase'] = null;
    $row['pilot_coverage_ok_after_purchase'] = true;
    $row['required_license'] = null;
    $row['unlock_status'] = 'AVAILABLE_FOR_DEVELOPMENT_TEST';
    $row['unlock_note'] = 'Development mode: all aircraft are visible. Purchase is limited only by budget.';
    $row['is_available_for_current_level'] = true;

    $aircraft[] = attach_aircraft_image_asset_path($row);
}

json_response([
    'level' => [
        'base_airport_icao_code' => $company['base_airport_icao_code'] ?? null,
        'base_tier' => 'DEVELOPMENT_OPEN_MARKET',
        'airport_size_tier' => null,
        'max_initial_aircraft_class' => 'ANY',
        'rule' => 'Development mode: all aircraft are visible. Purchase is budget-only.',
    ],
    'purchase_rule' => [
        'mode' => 'BUDGET_ONLY',
        'budget_amount' => number_format($budget, 2, '.', ''),
        'currency_code' => $company['currency_code'] ?? 'EUR',
        'rule' => 'Only the company budget can block aircraft purchase.',
    ],
    'pilot_coverage' => [
        'current_qualified_pilots' => null,
        'required_pilots_for_current_fleet' => null,
        'required_pilots_after_purchase' => null,
        'rule' => 'Disabled in development open-market mode.',
    ],
    'aircraft' => $aircraft,
]);

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
