<?php
declare(strict_types=1);

require __DIR__ . '/../../lib/bootstrap.php';
require __DIR__ . '/../../lib/session.php';

$session = require_auth_session();
$companyId = (int)$session['company_id'];
$pdo = db();

$crewColumns = existing_columns($pdo, 'scheduled_flight_instances', [
    'pilot_1_staff_id',
    'pilot_2_staff_id',
    'technician_staff_id',
]);

$busyCondition = '0 = 1';

if ($crewColumns !== []) {
    $checks = array_map(
        static fn (string $column): string => "f.`{$column}` = s.company_staff_id",
        $crewColumns
    );

    $busyCondition = implode(' OR ', $checks);
}

$sql = "
    SELECT
      s.*,
      CASE
        WHEN EXISTS (
          SELECT 1
          FROM scheduled_flight_instances f
          WHERE f.company_id = s.company_id
            AND f.status = 'IN_FLIGHT'
            AND ({$busyCondition})
        )
        THEN 'IN_FLIGHT'
        ELSE 'AVAILABLE'
      END AS operational_status
    FROM v_company_staff s
    WHERE s.company_id = :company_id
      AND s.employment_status <> 'DISMISSED'
    ORDER BY s.staff_role, s.display_name
";

$stmt = $pdo->prepare($sql);
$stmt->execute(['company_id' => $companyId]);

json_response(array_map(static function (array $row): array {
    return [
        'company_staff_id' => (int)$row['company_staff_id'],
        'company_id' => (int)$row['company_id'],
        'display_name' => $row['display_name'],
        'staff_role' => $row['staff_role'],
        'employment_status' => $row['employment_status'],
        'operational_status' => $row['operational_status'] ?? 'AVAILABLE',
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

function existing_columns(PDO $pdo, string $tableName, array $candidateColumns): array
{
    if ($candidateColumns === []) {
        return [];
    }

    $placeholders = implode(', ', array_fill(0, count($candidateColumns), '?'));
    $stmt = $pdo->prepare("
        SELECT COLUMN_NAME
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = ?
          AND COLUMN_NAME IN ({$placeholders})
    ");

    $stmt->execute(array_merge([$tableName], $candidateColumns));

    return array_map(static fn (array $row): string => $row['COLUMN_NAME'], $stmt->fetchAll());
}
