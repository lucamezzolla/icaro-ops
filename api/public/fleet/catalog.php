<?php
declare(strict_types=1);

require __DIR__ . '/../../lib/bootstrap.php';
require __DIR__ . '/../../lib/session.php';

$session = require_auth_session();
$companyId = (int)$session['company_id'];
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

$currentFleetCount = (int)$pdo
    ->query("SELECT COUNT(*) FROM company_aircraft WHERE company_id = " . (int)$companyId)
    ->fetchColumn();

$currentQualifiedPilots = count_qualified_pilots($pdo, $companyId, 'C208_TYPE');

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

/*
 * Current-level catalog.
 * Early development fallback: show only starter aircraft available now.
 * Concorde and future aircraft stay locked and hidden from the buy list.
 */
$starterModelCodes = [
    'C208B_GRAND_CARAVAN_EX',
];

$placeholders = implode(',', array_fill(0, count($starterModelCodes), '?'));

$sql = "
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
      {$priceColumn} AS new_purchase_price
    FROM aircraft_models
    WHERE model_code IN ({$placeholders})
      AND model_code <> 'CONCORDE'
    ORDER BY {$priceColumn}, manufacturer, model_name
";

$stmt = $pdo->prepare($sql);
$stmt->execute($starterModelCodes);

$aircraft = [];

foreach ($stmt->fetchAll() as $row) {
    $requiredAfterPurchase = ($currentFleetCount + 1) * 2;

    $row['currency_code'] = $company['currency_code'];
    $row['current_qualified_pilots'] = $currentQualifiedPilots;
    $row['required_pilots_after_purchase'] = $requiredAfterPurchase;
    $row['pilot_coverage_ok_after_purchase'] = $currentQualifiedPilots >= $requiredAfterPurchase;
    $row['unlock_status'] = 'AVAILABLE_FOR_CURRENT_LEVEL';
    $row['unlock_note'] = 'Available for the current early-game operating level.';

    $aircraft[] = $row;
}

json_response([
    'level' => [
        'base_airport_icao_code' => $company['base_airport_icao_code'] ?? null,
        'base_tier' => 'EARLY_GAME',
        'airport_size_tier' => null,
        'max_initial_aircraft_class' => 'LIGHT_COMMERCIAL',
        'rule' => 'Only aircraft unlocked for the current company/base level are shown in the buy dialog.',
    ],
    'pilot_coverage' => [
        'current_qualified_pilots' => $currentQualifiedPilots,
        'required_pilots_for_current_fleet' => $currentFleetCount * 2,
        'required_pilots_after_purchase' => ($currentFleetCount + 1) * 2,
        'rule' => 'Pilots are a qualified company pool. Each operational aircraft requires two active qualified pilots.',
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

function count_qualified_pilots(PDO $pdo, int $companyId, string $typeRating): int
{
    $stmt = $pdo->prepare("
        SELECT COUNT(DISTINCT s.id)
        FROM company_staff s
        WHERE s.company_id = :company_id
          AND s.staff_role = 'PILOT'
          AND s.employment_status = 'ACTIVE'
          AND EXISTS (
            SELECT 1
            FROM company_staff_licenses l
            WHERE l.company_staff_id = s.id
              AND l.license_code = 'CPL'
          )
          AND EXISTS (
            SELECT 1
            FROM company_staff_licenses l
            WHERE l.company_staff_id = s.id
              AND l.license_code = :type_rating
          )
    ");
    $stmt->execute([
        'company_id' => $companyId,
        'type_rating' => $typeRating,
    ]);

    return (int)$stmt->fetchColumn();
}
