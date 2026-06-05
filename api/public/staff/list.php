<?php
declare(strict_types=1);

require __DIR__ . '/../../lib/bootstrap.php';
require __DIR__ . '/../../lib/session.php';

$session = require_auth_session();
$companyId = (int)$session['company_id'];

$stmt = db()->prepare("
    SELECT
      id,
      id AS staff_id,
      id AS company_staff_id,
      company_id,

      first_name,
      last_name,
      display_name,

      staff_role,
      employment_status,
      assigned_base_icao_code,
      age_years,
      experience_level,

      fear_score,
      courage_score,
      stress_tolerance_score,
      stress_tolerance_score AS stress_score,
      discipline_score,
      teamwork_score,
      reliability_score,
      ambition_score,
      fatigue_risk_score,
      fatigue_score,

      flight_hours_total,
      aircraft_maintenance_hours_total,

      salary_per_flight,
      daily_retainer,
      revenue_share_percent,
      currency_code,

      hired_at_utc,
      dismissed_at_utc
    FROM company_staff
    WHERE company_id = :company_id
    ORDER BY
      CASE staff_role
        WHEN 'PILOT' THEN 1
        WHEN 'TECHNICIAN' THEN 2
        ELSE 3
      END,
      display_name
");
$stmt->execute(['company_id' => $companyId]);

json_response([
    'staff' => $stmt->fetchAll()
]);
