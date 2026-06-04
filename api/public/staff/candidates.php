<?php
declare(strict_types=1);

require __DIR__ . '/../../lib/bootstrap.php';
require __DIR__ . '/../../lib/session.php';

require_auth_session();

$role = strtoupper(trim((string)($_GET['role'] ?? '')));

$sql = "
    SELECT *
    FROM v_staff_candidates_available
";

$params = [];

if ($role !== '') {
    if (!in_array($role, ['PILOT', 'TECHNICIAN'], true)) {
        json_response(['error' => 'INVALID_ROLE'], 422);
    }

    $sql .= " WHERE staff_role = :role";
    $params['role'] = $role;
}

$sql .= " ORDER BY staff_role, reliability_score DESC, display_name";

$stmt = db()->prepare($sql);
$stmt->execute($params);

json_response(array_map(static function (array $row): array {
    return [
        'candidate_id' => (int)$row['candidate_id'],
        'display_name' => $row['display_name'],
        'staff_role' => $row['staff_role'],
        'home_region_code' => $row['home_region_code'],
        'preferred_base_icao_code' => $row['preferred_base_icao_code'],
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
        'hiring_bonus' => $row['hiring_bonus'],
        'morale_score' => (int)$row['morale_score'],
        'licenses_summary' => $row['licenses_summary'] ?? '',
    ];
}, $stmt->fetchAll()));
