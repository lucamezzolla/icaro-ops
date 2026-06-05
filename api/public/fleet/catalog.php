<?php
declare(strict_types=1);

require __DIR__ . '/../../lib/bootstrap.php';
require __DIR__ . '/../../lib/session.php';

$session = require_auth_session();
$companyId = (int)$session['company_id'];
$pdo = db();

$companyStmt = $pdo->prepare("SELECT currency_code FROM companies WHERE id = :company_id LIMIT 1");
$companyStmt->execute(['company_id' => $companyId]);
$company = $companyStmt->fetch() ?: ['currency_code' => 'EUR'];

$currentFleetCount = (int)$pdo->query("SELECT COUNT(*) FROM company_aircraft WHERE company_id = " . (int)$companyId)->fetchColumn();
$currentQualifiedPilots = count_qualified_pilots($pdo, $companyId, 'C208_TYPE');

$stmt = $pdo->query("
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
      base_purchase_price AS new_purchase_price
    FROM aircraft_models
    ORDER BY base_purchase_price, manufacturer, model_name
");

$aircraft = [];
foreach ($stmt->fetchAll() as $row) {
    $requiredAfterPurchase = ($currentFleetCount + 1) * 2;
    $row['currency_code'] = $company['currency_code'];
    $row['current_qualified_pilots'] = $currentQualifiedPilots;
    $row['required_pilots_after_purchase'] = $requiredAfterPurchase;
    $row['pilot_coverage_ok_after_purchase'] = $currentQualifiedPilots >= $requiredAfterPurchase;
    $aircraft[] = $row;
}

json_response([
    'pilot_coverage' => [
        'current_qualified_pilots' => $currentQualifiedPilots,
        'required_pilots_for_current_fleet' => $currentFleetCount * 2,
        'required_pilots_after_purchase' => ($currentFleetCount + 1) * 2,
        'rule' => 'Pilots are a qualified company pool. Each operational aircraft requires two active qualified pilots.',
    ],
    'aircraft' => $aircraft,
]);

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
