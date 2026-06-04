<?php
declare(strict_types=1);

require __DIR__ . '/../../lib/bootstrap.php';
require __DIR__ . '/../../lib/session.php';

$session = require_auth_session();
$companyId = $session['company_id'];

$stmt = db()->prepare("
    SELECT *
    FROM v_company_staff
    WHERE company_id = :company_id
      AND employment_status <> 'DISMISSED'
    ORDER BY staff_role, display_name
");

$stmt->execute(['company_id' => $companyId]);

json_response(array_map(static function (array $row): array {
    return [
        'company_staff_id' => (int)$row['company_staff_id'],
        'company_id' => (int)$row['company_id'],
        'display_name' => $row['display_name'],
        'staff_role' => $row['staff_role'],
        'employment_status' => $row['employment_status'],
        'assigned_base_icao_code' => $row['assigned_base_icao_code'],
        'age_years' => (int)$row['age_years'],
        'experience_level' => $row['experience_level'],
        'fear_score' => (int)$row['fear_score'],
        'courage_score' => (int)$row['courage_score'],
        'stress_tolerance_score' => (int)$row['stress_tolerance_score'],
        'discipline_score' => (int)$row['discipline_score'],
        'teamwork_score' => (int)$row['teamwork_score'],
        'reliability_score' => (int)$row['reliability_score'],
        'ambition_score' => (int)$row['ambition_score'],
        'fatigue_risk_score' => (int)$row['fatigue_risk_score'],
        'flight_hours_total' => (int)$row['flight_hours_total'],
        'aircraft_maintenance_hours_total' => (int)$row['aircraft_maintenance_hours_total'],
        'salary_per_flight' => $row['salary_per_flight'],
        'daily_retainer' => $row['daily_retainer'],
        'revenue_share_percent' => $row['revenue_share_percent'],
        'currency_code' => $row['currency_code'],
        'morale_score' => (int)$row['morale_score'],
        'fatigue_score' => (int)$row['fatigue_score'],
        'licenses_summary' => $row['licenses_summary'] ?? '',
    ];
}, $stmt->fetchAll()));
