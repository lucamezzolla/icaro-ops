<?php
declare(strict_types=1);

require __DIR__ . '/../../lib/bootstrap.php';
require __DIR__ . '/../../lib/session.php';

$session = require_auth_session();
$companyId = (int)$session['company_id'];

$role = strtoupper(trim((string)($_GET['role'] ?? 'ALL')));
$query = trim((string)($_GET['q'] ?? ''));
$fleetOnly = in_array(strtolower(trim((string)($_GET['fleetOnly'] ?? $_GET['fleet_only'] ?? '0'))), ['1', 'true', 'yes', 'on'], true);

$pdo = db();

if ($role === 'PILOT' && $fleetOnly) {
    ensure_fleet_pilot_candidates($pdo, $companyId);
}

$fleetRatingCodes = $fleetOnly ? get_company_fleet_rating_codes($pdo, $companyId) : [];

$where = ["c.status = 'AVAILABLE'"];
$params = [];

if (in_array($role, ['PILOT', 'TECHNICIAN'], true)) {
    $where[] = 'c.staff_role = :role';
    $params['role'] = $role;
}

if ($query !== '') {
    $queryLike = '%' . $query . '%';
    $queryFields = [
        'c.display_name',
        'c.first_name',
        'c.last_name',
        'c.home_region_code',
        'c.experience_level',
    ];

    $queryParts = [];
    foreach ($queryFields as $index => $field) {
        $key = 'query_field_' . $index;
        $queryParts[] = $field . ' LIKE :' . $key;
        $params[$key] = $queryLike;
    }

    $params['query_license_code'] = $queryLike;
    $params['query_license_name'] = $queryLike;
    $params['query_license_description'] = $queryLike;

    $queryParts[] = "EXISTS (
        SELECT 1
        FROM staff_candidate_licenses ql
        LEFT JOIN staff_license_types qlt
          ON qlt.code = ql.license_code
        WHERE ql.candidate_id = c.id
          AND (
            ql.license_code LIKE :query_license_code
            OR qlt.name LIKE :query_license_name
            OR qlt.description LIKE :query_license_description
          )
    )";

    $where[] = '(' . implode("
        OR ", $queryParts) . ')';
}

$fleetJoin = '';
$fleetSelect = "'' AS fleet_matching_licenses, 0 AS fleet_rating_match_count";
$orderFleet = '';

if ($fleetOnly) {
    if (!$fleetRatingCodes) {
        json_response([
            'candidates' => [],
            'fleet_rating_codes' => [],
            'message' => 'No owned aircraft type ratings found yet.'
        ]);
    }

    $existsPlaceholders = [];
    $joinPlaceholders = [];
    foreach ($fleetRatingCodes as $index => $code) {
        $existsKey = 'fleet_exists_rating_' . $index;
        $joinKey = 'fleet_join_rating_' . $index;
        $existsPlaceholders[] = ':' . $existsKey;
        $joinPlaceholders[] = ':' . $joinKey;
        $params[$existsKey] = $code;
        $params[$joinKey] = $code;
    }

    $existsInList = implode(', ', $existsPlaceholders);
    $joinInList = implode(', ', $joinPlaceholders);
    $where[] = "EXISTS (
        SELECT 1
        FROM staff_candidate_licenses fl
        WHERE fl.candidate_id = c.id
          AND fl.license_code IN ({$existsInList})
    )";

    $fleetJoin = "
      LEFT JOIN staff_candidate_licenses fleet_license
        ON fleet_license.candidate_id = c.id
       AND fleet_license.license_code IN ({$joinInList})
    ";
    $fleetSelect = "
      GROUP_CONCAT(DISTINCT fleet_license.license_code ORDER BY fleet_license.license_code SEPARATOR ', ') AS fleet_matching_licenses,
      COUNT(DISTINCT fleet_license.license_code) AS fleet_rating_match_count
    ";
    $orderFleet = 'fleet_rating_match_count DESC,';
}

$whereSql = implode("\n      AND ", $where);

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
      GROUP_CONCAT(DISTINCT l.license_code ORDER BY l.license_code SEPARATOR ', ') AS licenses,
      {$fleetSelect}
    FROM staff_candidates c
    LEFT JOIN staff_candidate_licenses l
      ON l.candidate_id = c.id
    {$fleetJoin}
    WHERE {$whereSql}
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
      {$orderFleet}
      CASE c.staff_role WHEN 'PILOT' THEN 1 WHEN 'TECHNICIAN' THEN 2 ELSE 3 END,
      c.reliability_score DESC,
      c.home_region_code,
      c.display_name
    LIMIT 80
");
$stmt->execute($params);

json_response([
    'candidates' => $stmt->fetchAll(),
    'fleet_rating_codes' => $fleetRatingCodes,
]);

function ensure_fleet_pilot_candidates(PDO $pdo, int $companyId): void
{
    $ownedModels = get_company_owned_aircraft_models($pdo, $companyId);
    if (!$ownedModels) {
        return;
    }

    $base = get_company_base_airport($pdo, $companyId);
    $names = [
        ['Amelia', 'Stone', 'EUROPE'],
        ['Noah', 'Ibrahim', 'MIDDLE_EAST'],
        ['Sofia', 'Kowalska', 'EUROPE'],
        ['Mateo', 'Okafor', 'AFRICA'],
        ['Yuki', 'Santos', 'ASIA'],
        ['Amina', 'Williams', 'AFRICA'],
        ['Lars', 'Tanaka', 'EUROPE'],
        ['Grace', 'Silva', 'NORTH_AMERICA'],
        ['Arjun', 'Rojas', 'ASIA'],
        ['Marta', 'Taylor', 'OCEANIA'],
    ];

    foreach ($ownedModels as $model) {
        $ratingCode = aircraft_type_rating_code($model);
        $modelLabel = trim((string)($model['manufacturer'] ?? '') . ' ' . (string)($model['model_name'] ?? ''));
        $ownedCount = max(1, (int)($model['owned_count'] ?? 1));
        $targetAvailable = max(2, $ownedCount * 2);

        ensure_staff_license_type($pdo, $ratingCode, $modelLabel);
        $available = count_available_pilot_candidates_for_rating($pdo, $ratingCode);

        while ($available < $targetAvailable) {
            $seed = ((int)($model['aircraft_model_id'] ?? 1) + $available) % count($names);
            [$firstName, $lastName, $region] = $names[$seed];
            $suffix = strtoupper(substr(preg_replace('/[^A-Z0-9]/', '', $ratingCode), 0, 8));
            $displayName = $firstName . ' ' . $lastName . ' ' . $suffix . '-' . ($available + 1);

            $candidateId = insert_generated_pilot_candidate(
                $pdo,
                $firstName,
                $lastName . ' ' . $suffix . '-' . ($available + 1),
                $displayName,
                $region,
                $base,
                (int)($model['aircraft_model_id'] ?? 1),
                $available
            );

            add_candidate_license($pdo, $candidateId, 'CPL', 76 + (($available + 3) % 18));
            add_candidate_license($pdo, $candidateId, 'IR', 70 + (($available + 5) % 16));
            add_candidate_license($pdo, $candidateId, $ratingCode, 72 + (($available + 7) % 22));

            $available++;
        }
    }
}

function get_company_owned_aircraft_models(PDO $pdo, int $companyId): array
{
    $stmt = $pdo->prepare("
        SELECT
          am.id AS aircraft_model_id,
          am.manufacturer,
          am.model_name,
          am.model_code,
          am.icao_type_code,
          COUNT(ca.id) AS owned_count
        FROM company_aircraft ca
        JOIN aircraft_models am
          ON am.id = ca.aircraft_model_id
        WHERE ca.company_id = :company_id
          AND ca.status <> 'RETIRED'
        GROUP BY
          am.id,
          am.manufacturer,
          am.model_name,
          am.model_code,
          am.icao_type_code
        ORDER BY am.manufacturer, am.model_name
    ");
    $stmt->execute(['company_id' => $companyId]);
    return $stmt->fetchAll();
}

function get_company_fleet_rating_codes(PDO $pdo, int $companyId): array
{
    $codes = [];
    foreach (get_company_owned_aircraft_models($pdo, $companyId) as $model) {
        $codes[] = aircraft_type_rating_code($model);
    }
    return array_values(array_unique($codes));
}

function aircraft_type_rating_code(array $model): string
{
    $modelCode = strtoupper(trim((string)($model['model_code'] ?? '')));
    $icao = strtoupper(trim((string)($model['icao_type_code'] ?? '')));

    if ($modelCode === 'C208B_GRAND_CARAVAN_EX') {
        return 'C208_TYPE';
    }
    if ($modelCode === 'DHC6_TWIN_OTTER_400') {
        return 'DHC6_TYPE';
    }
    if ($modelCode === 'ATR42_600') {
        return 'ATR42_TYPE';
    }
    if ($icao !== '') {
        return preg_replace('/[^A-Z0-9_]/', '', $icao) . '_TYPE';
    }
    return preg_replace('/[^A-Z0-9_]/', '', $modelCode) . '_TYPE';
}

function ensure_staff_license_type(PDO $pdo, string $ratingCode, string $modelLabel): void
{
    $stmt = $pdo->prepare("
        INSERT IGNORE INTO staff_license_types (
          code,
          name,
          staff_role,
          description,
          is_required_for_commercial_ops,
          is_active
        ) VALUES (
          :code,
          :name,
          'PILOT',
          :description,
          TRUE,
          TRUE
        )
        ON DUPLICATE KEY UPDATE
          name = VALUES(name),
          description = VALUES(description),
          staff_role = 'PILOT',
          is_required_for_commercial_ops = TRUE,
          is_active = TRUE
    ");
    $stmt->execute([
        'code' => $ratingCode,
        'name' => $ratingCode . ' Type Rating',
        'description' => 'Game type rating required to operate ' . ($modelLabel !== '' ? $modelLabel : $ratingCode) . '.',
    ]);
}

function count_available_pilot_candidates_for_rating(PDO $pdo, string $ratingCode): int
{
    $stmt = $pdo->prepare("
        SELECT COUNT(DISTINCT c.id) AS candidate_count
        FROM staff_candidates c
        JOIN staff_candidate_licenses rating
          ON rating.candidate_id = c.id
         AND rating.license_code = :rating_code
        JOIN staff_candidate_licenses cpl
          ON cpl.candidate_id = c.id
         AND cpl.license_code = 'CPL'
        WHERE c.staff_role = 'PILOT'
          AND c.status = 'AVAILABLE'
    ");
    $stmt->execute(['rating_code' => $ratingCode]);
    return (int)($stmt->fetch()['candidate_count'] ?? 0);
}

function get_company_base_airport(PDO $pdo, int $companyId): string
{
    $stmt = $pdo->prepare("SELECT base_airport_icao_code FROM companies WHERE id = :company_id LIMIT 1");
    $stmt->execute(['company_id' => $companyId]);
    $base = strtoupper(trim((string)($stmt->fetch()['base_airport_icao_code'] ?? '')));
    return $base !== '' ? $base : 'LIRA';
}

function insert_generated_pilot_candidate(
    PDO $pdo,
    string $firstName,
    string $lastName,
    string $displayName,
    string $region,
    string $base,
    int $modelId,
    int $sequence
): int {
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
          generated_at_utc,
          expires_at_utc
        ) VALUES (
          :first_name,
          :last_name,
          :display_name,
          'PILOT',
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
          0,
          :salary_per_flight,
          :daily_retainer,
          :revenue_share_percent,
          'EUR',
          :hiring_bonus,
          72,
          UTC_TIMESTAMP(),
          NULL
        )
    ");

    $stmt->execute([
        'first_name' => $firstName,
        'last_name' => $lastName,
        'display_name' => $displayName,
        'home_region_code' => $region,
        'preferred_base_icao_code' => $base,
        'age_years' => 26 + (($modelId + $sequence) % 24),
        'experience_level' => (($modelId + $sequence) % 3 === 0) ? 'SENIOR' : (((($modelId + $sequence) % 3) === 1) ? 'INTERMEDIATE' : 'JUNIOR'),
        'fear_score' => 10 + (($modelId + $sequence) % 20),
        'courage_score' => 66 + (($modelId + $sequence) % 25),
        'stress_tolerance_score' => 65 + (($modelId + $sequence) % 25),
        'discipline_score' => 64 + (($modelId + $sequence) % 24),
        'teamwork_score' => 62 + (($modelId + $sequence) % 28),
        'reliability_score' => 68 + (($modelId + $sequence) % 24),
        'ambition_score' => 45 + (($modelId + $sequence) % 35),
        'fatigue_risk_score' => 12 + (($modelId + $sequence) % 26),
        'flight_hours_total' => 450 + (($modelId + $sequence) * 37),
        'salary_per_flight' => 360 + (($modelId + $sequence) % 12) * 45,
        'daily_retainer' => 85 + (($modelId + $sequence) % 8) * 15,
        'revenue_share_percent' => 0,
        'hiring_bonus' => 700 + (($modelId + $sequence) % 10) * 120,
    ]);

    return (int)$pdo->lastInsertId();
}

function add_candidate_license(PDO $pdo, int $candidateId, string $licenseCode, int $proficiency): void
{
    $stmt = $pdo->prepare("
        INSERT IGNORE INTO staff_candidate_licenses (
          candidate_id,
          license_code,
          proficiency_score,
          issued_at_utc,
          expires_at_utc
        ) VALUES (
          :candidate_id,
          :license_code,
          :proficiency_score,
          UTC_TIMESTAMP(),
          NULL
        )
    ");
    $stmt->execute([
        'candidate_id' => $candidateId,
        'license_code' => $licenseCode,
        'proficiency_score' => max(0, min(100, $proficiency)),
    ]);
}
