<?php
declare(strict_types=1);

require __DIR__ . '/../../lib/bootstrap.php';
require __DIR__ . '/../../lib/session.php';

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    json_response(['error' => 'METHOD_NOT_ALLOWED'], 405);
}

$session = require_auth_session();
$companyId = (int)$session['company_id'];
$payload = read_json_body();

$candidateId = (int)($payload['candidate_id'] ?? 0);

if ($candidateId <= 0) {
    json_response(['error' => 'INVALID_CANDIDATE_ID'], 422);
}

$pdo = db();

try {
    $pdo->beginTransaction();

    $stmt = $pdo->prepare("
        SELECT *
        FROM staff_candidates
        WHERE id = :id
          AND status = 'AVAILABLE'
        LIMIT 1
        FOR UPDATE
    ");
    $stmt->execute(['id' => $candidateId]);
    $candidate = $stmt->fetch();

    if (!$candidate) {
        $pdo->rollBack();
        json_response(['error' => 'CANDIDATE_NOT_AVAILABLE'], 409);
    }

    $companyStmt = $pdo->prepare("
        SELECT base_airport_icao_code
        FROM companies
        WHERE id = :company_id
        LIMIT 1
    ");
    $companyStmt->execute(['company_id' => $companyId]);
    $company = $companyStmt->fetch();

    $base = $candidate['preferred_base_icao_code'] ?: ($company['base_airport_icao_code'] ?? 'LIRA');

    $insert = $pdo->prepare("
        INSERT INTO company_staff (
          company_id,
          source_candidate_id,
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
          morale_score,
          fatigue_score
        ) VALUES (
          :company_id,
          :source_candidate_id,
          :first_name,
          :last_name,
          :display_name,
          :staff_role,
          'ACTIVE',
          :assigned_base_icao_code,
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
          :morale_score,
          0
        )
    ");
    $insert->execute([
        'company_id' => $companyId,
        'source_candidate_id' => $candidateId,
        'first_name' => $candidate['first_name'],
        'last_name' => $candidate['last_name'],
        'display_name' => $candidate['display_name'],
        'staff_role' => $candidate['staff_role'],
        'assigned_base_icao_code' => $base,
        'age_years' => $candidate['age_years'],
        'experience_level' => $candidate['experience_level'],
        'fear_score' => $candidate['fear_score'],
        'courage_score' => $candidate['courage_score'],
        'stress_tolerance_score' => $candidate['stress_tolerance_score'],
        'discipline_score' => $candidate['discipline_score'],
        'teamwork_score' => $candidate['teamwork_score'],
        'reliability_score' => $candidate['reliability_score'],
        'ambition_score' => $candidate['ambition_score'],
        'fatigue_risk_score' => $candidate['fatigue_risk_score'],
        'flight_hours_total' => $candidate['flight_hours_total'],
        'aircraft_maintenance_hours_total' => $candidate['aircraft_maintenance_hours_total'],
        'salary_per_flight' => $candidate['salary_per_flight'],
        'daily_retainer' => $candidate['daily_retainer'],
        'revenue_share_percent' => $candidate['revenue_share_percent'],
        'currency_code' => $candidate['currency_code'],
        'morale_score' => $candidate['morale_score'],
    ]);

    $staffId = (int)$pdo->lastInsertId();

    $licenses = $pdo->prepare("
        INSERT IGNORE INTO company_staff_licenses (
          company_staff_id,
          license_code,
          proficiency_score,
          issued_at_utc,
          expires_at_utc
        )
        SELECT
          :staff_id,
          license_code,
          proficiency_score,
          issued_at_utc,
          expires_at_utc
        FROM staff_candidate_licenses
        WHERE candidate_id = :candidate_id
    ");
    $licenses->execute([
        'staff_id' => $staffId,
        'candidate_id' => $candidateId,
    ]);

    $pdo->prepare("
        UPDATE staff_candidates
        SET status = 'HIRED'
        WHERE id = :id
    ")->execute(['id' => $candidateId]);

    $pdo->commit();

    json_response([
        'status' => 'HIRED',
        'company_staff_id' => $staffId,
        'display_name' => $candidate['display_name'],
        'staff_role' => $candidate['staff_role'],
    ], 201);
} catch (Throwable $exception) {
    if ($pdo->inTransaction()) {
        $pdo->rollBack();
    }

    json_response([
        'error' => 'HIRE_FAILED',
        'message' => $exception->getMessage(),
    ], 500);
}
