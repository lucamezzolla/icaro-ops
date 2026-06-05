<?php
declare(strict_types=1);

require __DIR__ . '/../../lib/bootstrap.php';
require __DIR__ . '/../../lib/session.php';

$session = require_auth_session();
$companyId = (int)$session['company_id'];

$pdo = db();

$companyStmt = $pdo->prepare("
    SELECT
      id,
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
    'world_region_code' => 'EUROPE',
];

$company['world_region_code'] = $company['world_region_code'] ?? 'EUROPE';

ensure_staff_candidate_market($pdo, $companyId, $company);

$stmt = $pdo->prepare("
    SELECT
      c.id,
      c.id AS candidate_id,
      c.first_name,
      c.last_name,
      c.display_name,
      c.staff_role,
      c.status,
      c.home_region_code,
      c.preferred_base_icao_code,
      c.age_years,
      c.experience_level,
      c.fear_score,
      c.courage_score,
      c.stress_tolerance_score,
      c.stress_tolerance_score AS stress_score,
      c.discipline_score,
      c.teamwork_score,
      c.reliability_score,
      c.ambition_score,
      c.fatigue_risk_score,
      c.flight_hours_total,
      c.aircraft_maintenance_hours_total,
      c.salary_per_flight,
      c.daily_retainer,
      c.revenue_share_percent,
      c.currency_code,
      c.hiring_bonus,
      c.morale_score,
      c.generated_at_utc,
      c.expires_at_utc,
      GROUP_CONCAT(l.license_code ORDER BY l.license_code SEPARATOR ', ') AS licenses
    FROM staff_candidates c
    LEFT JOIN staff_candidate_licenses l
      ON l.candidate_id = c.id
    WHERE c.status = 'AVAILABLE'
      AND (c.expires_at_utc IS NULL OR c.expires_at_utc > UTC_TIMESTAMP())
    GROUP BY c.id
    ORDER BY
      CASE c.staff_role
        WHEN 'PILOT' THEN 1
        WHEN 'TECHNICIAN' THEN 2
        ELSE 3
      END,
      CASE
        WHEN SUM(l.license_code = 'C208_TYPE') > 0 THEN 1
        ELSE 2
      END,
      c.reliability_score DESC,
      c.display_name
    LIMIT 40
");
$stmt->execute();

$candidates = $stmt->fetchAll();

json_response([
    'coverage' => staff_coverage($pdo, $companyId),
    'candidates' => $candidates,
]);

function ensure_staff_candidate_market(PDO $pdo, int $companyId, array $company): void
{
    $coverage = staff_coverage($pdo, $companyId);

    /*
     * Candidate market policy:
     * - keep at least 6 C208-qualified pilot candidates around
     * - if company needs more pilots, keep need + 3 candidates
     * - keep at least 3 C208 maintenance technician candidates around
     * - if company needs more technicians, keep need + 2 candidates
     */
    $targetPilotCandidates = max(
        6,
        (int)$coverage['pilot_coverage']['missing_c208_pilots'] + 3
    );

    $targetTechnicianCandidates = max(
        3,
        (int)$coverage['technician_coverage']['missing_c208_technicians'] + 2
    );

    $availablePilotCandidates = count_available_candidates_with_license($pdo, 'PILOT', 'C208_TYPE');
    $availableTechnicianCandidates = count_available_candidates_with_license($pdo, 'TECHNICIAN', 'C208_MAINT');

    for ($i = $availablePilotCandidates; $i < $targetPilotCandidates; $i++) {
        create_candidate($pdo, $company, 'PILOT');
    }

    for ($i = $availableTechnicianCandidates; $i < $targetTechnicianCandidates; $i++) {
        create_candidate($pdo, $company, 'TECHNICIAN');
    }
}

function staff_coverage(PDO $pdo, int $companyId): array
{
    $aircraftCount = (int)$pdo
        ->query("SELECT COUNT(*) FROM company_aircraft WHERE company_id = " . (int)$companyId)
        ->fetchColumn();

    $qualifiedC208Pilots = count_qualified_staff($pdo, $companyId, 'PILOT', 'C208_TYPE', true);
    $requiredC208PilotsCurrentFleet = $aircraftCount * 2;
    $requiredC208PilotsAfterNextPurchase = ($aircraftCount + 1) * 2;

    $qualifiedC208Technicians = count_qualified_staff($pdo, $companyId, 'TECHNICIAN', 'C208_MAINT', false);
    $requiredTechniciansCurrentFleet = max(1, (int)ceil(max(1, $aircraftCount) / 3));
    $requiredTechniciansAfterNextPurchase = max(1, (int)ceil(max(1, $aircraftCount + 1) / 3));

    return [
        'pilot_coverage' => [
            'rule' => '2 active C208-qualified pilots are required for each operational aircraft.',
            'current_aircraft' => $aircraftCount,
            'qualified_c208_pilots' => $qualifiedC208Pilots,
            'required_for_current_fleet' => $requiredC208PilotsCurrentFleet,
            'required_after_next_purchase' => $requiredC208PilotsAfterNextPurchase,
            'missing_c208_pilots' => max(0, $requiredC208PilotsAfterNextPurchase - $qualifiedC208Pilots),
        ],
        'technician_coverage' => [
            'rule' => 'Recommended coverage is 1 C208-qualified technician every 3 aircraft.',
            'current_aircraft' => $aircraftCount,
            'qualified_c208_technicians' => $qualifiedC208Technicians,
            'required_for_current_fleet' => $requiredTechniciansCurrentFleet,
            'required_after_next_purchase' => $requiredTechniciansAfterNextPurchase,
            'missing_c208_technicians' => max(0, $requiredTechniciansAfterNextPurchase - $qualifiedC208Technicians),
            'blocks_purchase' => false,
        ],
    ];
}

function count_qualified_staff(PDO $pdo, int $companyId, string $role, string $licenseCode, bool $requiresCpl): int
{
    $cplClause = $requiresCpl
        ? "AND EXISTS (
            SELECT 1
            FROM company_staff_licenses cpl
            WHERE cpl.company_staff_id = s.id
              AND cpl.license_code = 'CPL'
          )"
        : "";

    $stmt = $pdo->prepare("
        SELECT COUNT(DISTINCT s.id)
        FROM company_staff s
        WHERE s.company_id = :company_id
          AND s.staff_role = :role
          AND s.employment_status = 'ACTIVE'
          {$cplClause}
          AND EXISTS (
            SELECT 1
            FROM company_staff_licenses l
            WHERE l.company_staff_id = s.id
              AND l.license_code = :license_code
          )
    ");
    $stmt->execute([
        'company_id' => $companyId,
        'role' => $role,
        'license_code' => $licenseCode,
    ]);

    return (int)$stmt->fetchColumn();
}

function count_available_candidates_with_license(PDO $pdo, string $role, string $licenseCode): int
{
    $stmt = $pdo->prepare("
        SELECT COUNT(DISTINCT c.id)
        FROM staff_candidates c
        JOIN staff_candidate_licenses l
          ON l.candidate_id = c.id
        WHERE c.staff_role = :role
          AND c.status = 'AVAILABLE'
          AND (c.expires_at_utc IS NULL OR c.expires_at_utc > UTC_TIMESTAMP())
          AND l.license_code = :license_code
    ");
    $stmt->execute([
        'role' => $role,
        'license_code' => $licenseCode,
    ]);

    return (int)$stmt->fetchColumn();
}

function create_candidate(PDO $pdo, array $company, string $role): void
{
    $names = candidate_name($role);
    $profile = candidate_profile($role);

    $stmt = $pdo->prepare("
        INSERT INTO staff_candidates (
          first_name,
          last_name,
          display_name,
          staff_role,
          status,
          home_region_code,
          preferred_base_icao_code,
          age_years,
          experience_level,
          fear_score,
          courage_score,
          stress_tolerance_score,
          discipline_score,
          teamwork_score,
          reliability_score,
          ambition_score,
          fatigue_risk_score,
          flight_hours_total,
          aircraft_maintenance_hours_total,
          salary_per_flight,
          daily_retainer,
          revenue_share_percent,
          currency_code,
          hiring_bonus,
          morale_score,
          expires_at_utc
        ) VALUES (
          :first_name,
          :last_name,
          :display_name,
          :staff_role,
          'AVAILABLE',
          :home_region_code,
          :preferred_base_icao_code,
          :age_years,
          :experience_level,
          :fear_score,
          :courage_score,
          :stress_tolerance_score,
          :discipline_score,
          :teamwork_score,
          :reliability_score,
          :ambition_score,
          :fatigue_risk_score,
          :flight_hours_total,
          :aircraft_maintenance_hours_total,
          :salary_per_flight,
          :daily_retainer,
          :revenue_share_percent,
          :currency_code,
          :hiring_bonus,
          :morale_score,
          DATE_ADD(UTC_TIMESTAMP(), INTERVAL 14 DAY)
        )
    ");

    $stmt->execute([
        'first_name' => $names['first_name'],
        'last_name' => $names['last_name'],
        'display_name' => $names['display_name'],
        'staff_role' => $role,
        'home_region_code' => $company['world_region_code'] ?? 'EUROPE',
        'preferred_base_icao_code' => $company['base_airport_icao_code'] ?? null,
        'age_years' => $profile['age_years'],
        'experience_level' => $profile['experience_level'],
        'fear_score' => $profile['fear_score'],
        'courage_score' => $profile['courage_score'],
        'stress_tolerance_score' => $profile['stress_tolerance_score'],
        'discipline_score' => $profile['discipline_score'],
        'teamwork_score' => $profile['teamwork_score'],
        'reliability_score' => $profile['reliability_score'],
        'ambition_score' => $profile['ambition_score'],
        'fatigue_risk_score' => $profile['fatigue_risk_score'],
        'flight_hours_total' => $profile['flight_hours_total'],
        'aircraft_maintenance_hours_total' => $profile['aircraft_maintenance_hours_total'],
        'salary_per_flight' => $profile['salary_per_flight'],
        'daily_retainer' => $profile['daily_retainer'],
        'revenue_share_percent' => $profile['revenue_share_percent'],
        'currency_code' => $company['currency_code'] ?? 'EUR',
        'hiring_bonus' => $profile['hiring_bonus'],
        'morale_score' => $profile['morale_score'],
    ]);

    $candidateId = (int)$pdo->lastInsertId();

    $licenses = $role === 'PILOT'
        ? ['CPL', 'IR', 'TURBOPROP_BASIC', 'C208_TYPE']
        : ['A_AND_P', 'TURBOPROP_MAINT', 'C208_MAINT'];

    foreach ($licenses as $licenseCode) {
        $licenseStmt = $pdo->prepare("
            INSERT IGNORE INTO staff_candidate_licenses (
              candidate_id,
              license_code,
              proficiency_score
            ) VALUES (
              :candidate_id,
              :license_code,
              :proficiency_score
            )
        ");
        $licenseStmt->execute([
            'candidate_id' => $candidateId,
            'license_code' => $licenseCode,
            'proficiency_score' => random_int(68, 90),
        ]);
    }
}

function candidate_name(string $role): array
{
    static $firstNames = [
        'Andrea', 'Bianca', 'Carlo', 'Diana', 'Enrico', 'Francesca',
        'Giorgio', 'Helena', 'Ivan', 'Laura', 'Matteo', 'Nora',
        'Oscar', 'Paola', 'Riccardo', 'Sara', 'Tobias', 'Valeria',
        'Yuri', 'Zoe'
    ];

    static $lastNames = [
        'Mariani', 'Greco', 'Costa', 'Ferrari', 'Romano', 'Moretti',
        'Rossi', 'Bianchi', 'Gallo', 'Fontana', 'Barbieri', 'Serra',
        'Rinaldi', 'Mancini', 'Conti', 'Villa', 'Leone', 'Fabbri'
    ];

    $first = $firstNames[array_rand($firstNames)];
    $last = $lastNames[array_rand($lastNames)];
    $suffix = random_int(100, 999);

    return [
        'first_name' => $first,
        'last_name' => $last,
        'display_name' => "{$first} {$last} {$suffix}",
    ];
}

function candidate_profile(string $role): array
{
    if ($role === 'PILOT') {
        return [
            'age_years' => random_int(27, 54),
            'experience_level' => random_int(1, 100) > 55 ? 'INTERMEDIATE' : 'JUNIOR',
            'fear_score' => random_int(8, 38),
            'courage_score' => random_int(58, 92),
            'stress_tolerance_score' => random_int(55, 90),
            'discipline_score' => random_int(58, 92),
            'teamwork_score' => random_int(55, 90),
            'reliability_score' => random_int(60, 94),
            'ambition_score' => random_int(45, 88),
            'fatigue_risk_score' => random_int(10, 45),
            'flight_hours_total' => random_int(450, 3200),
            'aircraft_maintenance_hours_total' => 0,
            'salary_per_flight' => random_int(220, 520),
            'daily_retainer' => random_int(25, 80),
            'revenue_share_percent' => random_int(0, 4),
            'hiring_bonus' => random_int(0, 400),
            'morale_score' => random_int(62, 86),
        ];
    }

    return [
        'age_years' => random_int(25, 58),
        'experience_level' => random_int(1, 100) > 50 ? 'INTERMEDIATE' : 'JUNIOR',
        'fear_score' => random_int(5, 35),
        'courage_score' => random_int(45, 80),
        'stress_tolerance_score' => random_int(55, 92),
        'discipline_score' => random_int(62, 95),
        'teamwork_score' => random_int(52, 88),
        'reliability_score' => random_int(60, 94),
        'ambition_score' => random_int(35, 75),
        'fatigue_risk_score' => random_int(10, 42),
        'flight_hours_total' => 0,
        'aircraft_maintenance_hours_total' => random_int(600, 6500),
        'salary_per_flight' => 0,
        'daily_retainer' => random_int(90, 210),
        'revenue_share_percent' => 0,
        'hiring_bonus' => random_int(0, 350),
        'morale_score' => random_int(62, 86),
    ];
}
