<?php
declare(strict_types=1);

require __DIR__ . '/../../lib/bootstrap.php';
require __DIR__ . '/../../lib/session.php';

require_auth_session();

$role = strtoupper(trim((string)($_GET['role'] ?? 'ALL')));

$pdo = db();

$where = "WHERE c.status = 'AVAILABLE'";
$params = [];

if (in_array($role, ['PILOT', 'TECHNICIAN'], true)) {
    $where .= " AND c.staff_role = :role";
    $params['role'] = $role;
}

$stmt = $pdo->prepare("
    SELECT
      c.id,
      c.id AS candidate_id,
      c.display_name,
      c.first_name,
      c.last_name,
      c.staff_role,
      c.status,
      c.home_region_code,
      c.preferred_base_icao_code,
      c.age_years,
      c.experience_level,
      c.reliability_score,
      c.teamwork_score,
      c.discipline_score,
      c.stress_tolerance_score,
      c.fatigue_risk_score,
      c.flight_hours_total,
      c.aircraft_maintenance_hours_total,
      c.salary_per_flight,
      c.daily_retainer,
      c.revenue_share_percent,
      c.currency_code,
      c.hiring_bonus,
      GROUP_CONCAT(l.license_code ORDER BY l.license_code SEPARATOR ', ') AS licenses
    FROM staff_candidates c
    LEFT JOIN staff_candidate_licenses l
      ON l.candidate_id = c.id
    {$where}
    GROUP BY
      c.id,
      c.display_name,
      c.first_name,
      c.last_name,
      c.staff_role,
      c.status,
      c.home_region_code,
      c.preferred_base_icao_code,
      c.age_years,
      c.experience_level,
      c.reliability_score,
      c.teamwork_score,
      c.discipline_score,
      c.stress_tolerance_score,
      c.fatigue_risk_score,
      c.flight_hours_total,
      c.aircraft_maintenance_hours_total,
      c.salary_per_flight,
      c.daily_retainer,
      c.revenue_share_percent,
      c.currency_code,
      c.hiring_bonus
    ORDER BY
      CASE c.staff_role WHEN 'PILOT' THEN 1 WHEN 'TECHNICIAN' THEN 2 ELSE 3 END,
      c.home_region_code,
      c.display_name
");
$stmt->execute($params);

json_response([
    'candidates' => $stmt->fetchAll(),
]);
