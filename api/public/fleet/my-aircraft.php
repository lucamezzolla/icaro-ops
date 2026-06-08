<?php
declare(strict_types=1);

require __DIR__ . '/../../lib/bootstrap.php';
require __DIR__ . '/../../lib/aircraft-images.php';
require __DIR__ . '/../../lib/session.php';

$session = require_auth_session();
$companyId = (int)$session['company_id'];
$pdo = db();

$stmt = $pdo->prepare("
    SELECT
      ca.id AS aircraft_id,
      ca.company_id,
      ca.registration_code,
      ca.serial_number,
      ca.manufacture_year,
      ca.ownership_status,
      ca.acquisition_type,
      ca.purchase_price,
      ca.current_market_value,
      ca.currency_code,
      ca.home_base_icao_code,
      ca.current_airport_icao_code,
      ca.condition_percent,
      ca.airframe_hours,
      ca.cycles_count,
      ca.status,
      ca.created_at_utc,

      am.id AS aircraft_model_id,
      am.manufacturer,
      am.model_name,
      am.model_code,
      am.icao_type_code,
      am.operation_role,
      am.passenger_capacity_standard,
      am.range_km,
      am.cruise_speed_kmh,
      am.fuel_burn_kg_per_hour,
      am.maintenance_cost_per_hour,
      am.image_asset_path
    FROM company_aircraft ca
    JOIN aircraft_models am
      ON am.id = ca.aircraft_model_id
    WHERE ca.company_id = :company_id
    ORDER BY ca.id
");
$stmt->execute(['company_id' => $companyId]);
$aircraft = attach_aircraft_image_asset_paths($stmt->fetchAll());

$qualifiedPilots = count_qualified_pilots($pdo, $companyId, 'C208_TYPE');
$totalAircraft = count($aircraft);
$requiredPilots = $totalAircraft * 2;

json_response([
    'summary' => [
        'total_aircraft' => $totalAircraft,
        'qualified_pilots' => $qualifiedPilots,
        'required_pilots_for_current_fleet' => $requiredPilots,
        'pilot_coverage_ok' => $qualifiedPilots >= $requiredPilots,
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
