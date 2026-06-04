<?php
declare(strict_types=1);

require __DIR__ . '/../../lib/bootstrap.php';
require __DIR__ . '/../../lib/session.php';

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    json_response(['error' => 'METHOD_NOT_ALLOWED'], 405);
}

$session = require_auth_session();
$companyId = $session['company_id'];

$payload = read_json_body();
$candidateId = (int)($payload['candidate_id'] ?? 0);

if ($candidateId <= 0) {
    json_response(['error' => 'VALIDATION_ERROR', 'message' => 'candidate_id is required.'], 422);
}

$pdo = db();

try {
    $pdo->beginTransaction();

    $companyStmt = $pdo->prepare("
        SELECT
          id,
          base_airport_icao_code,
          currency_code,
          budget_amount
        FROM companies
        WHERE id = :company_id
        LIMIT 1
        FOR UPDATE
    ");
    $companyStmt->execute(['company_id' => $companyId]);
    $company = $companyStmt->fetch();

    if (!$company) {
        $pdo->rollBack();
        json_response(['error' => 'COMPANY_NOT_FOUND'], 404);
    }

    $candidateStmt = $pdo->prepare("
        SELECT *
        FROM staff_candidates
        WHERE id = :candidate_id
          AND status = 'AVAILABLE'
        LIMIT 1
        FOR UPDATE
    ");
    $candidateStmt->execute(['candidate_id' => $candidateId]);
    $candidate = $candidateStmt->fetch();

    if (!$candidate) {
        $pdo->rollBack();
        json_response(['error' => 'CANDIDATE_NOT_AVAILABLE'], 404);
    }

    $hiringBonus = (float)$candidate['hiring_bonus'];
    $budget = (float)$company['budget_amount'];

    if ($budget < $hiringBonus) {
        $pdo->rollBack();
        json_response([
            'error' => 'INSUFFICIENT_FUNDS',
            'message' => 'Company budget is not enough for the hiring bonus.',
        ], 409);
    }

    $insertStaff = $pdo->prepare("
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

    $insertStaff->execute([
        'company_id' => $companyId,
        'source_candidate_id' => $candidateId,
        'first_name' => $candidate['first_name'],
        'last_name' => $candidate['last_name'],
        'display_name' => $candidate['display_name'],
        'staff_role' => $candidate['staff_role'],
        'assigned_base_icao_code' => $company['base_airport_icao_code'],
        'age_years' => (int)$candidate['age_years'],
        'experience_level' => $candidate['experience_level'],
        'fear_score' => (int)$candidate['fear_score'],
        'courage_score' => (int)$candidate['courage_score'],
        'stress_tolerance_score' => (int)$candidate['stress_tolerance_score'],
        'discipline_score' => (int)$candidate['discipline_score'],
        'teamwork_score' => (int)$candidate['teamwork_score'],
        'reliability_score' => (int)$candidate['reliability_score'],
        'ambition_score' => (int)$candidate['ambition_score'],
        'fatigue_risk_score' => (int)$candidate['fatigue_risk_score'],
        'flight_hours_total' => (int)$candidate['flight_hours_total'],
        'aircraft_maintenance_hours_total' => (int)$candidate['aircraft_maintenance_hours_total'],
        'salary_per_flight' => $candidate['salary_per_flight'],
        'daily_retainer' => $candidate['daily_retainer'],
        'revenue_share_percent' => $candidate['revenue_share_percent'],
        'currency_code' => $company['currency_code'],
        'morale_score' => (int)$candidate['morale_score'],
    ]);

    $companyStaffId = (int)$pdo->lastInsertId();

    $licenseStmt = $pdo->prepare("
        INSERT INTO company_staff_licenses (
          company_staff_id,
          license_code,
          proficiency_score,
          issued_at_utc,
          expires_at_utc
        )
        SELECT
          :company_staff_id,
          license_code,
          proficiency_score,
          issued_at_utc,
          expires_at_utc
        FROM staff_candidate_licenses
        WHERE candidate_id = :candidate_id
    ");
    $licenseStmt->execute([
        'company_staff_id' => $companyStaffId,
        'candidate_id' => $candidateId,
    ]);

    $candidateUpdate = $pdo->prepare("
        UPDATE staff_candidates
        SET status = 'HIRED'
        WHERE id = :candidate_id
    ");
    $candidateUpdate->execute(['candidate_id' => $candidateId]);

    if ($hiringBonus > 0) {
        $budgetUpdate = $pdo->prepare("
            UPDATE companies
            SET budget_amount = budget_amount - :hiring_bonus
            WHERE id = :company_id
        ");
        $budgetUpdate->execute([
            'hiring_bonus' => $hiringBonus,
            'company_id' => $companyId,
        ]);
    }

    $pdo->commit();

    json_response([
        'company_staff_id' => $companyStaffId,
        'candidate_id' => $candidateId,
        'display_name' => $candidate['display_name'],
        'staff_role' => $candidate['staff_role'],
        'hiring_bonus' => number_format($hiringBonus, 2, '.', ''),
        'status' => 'ACTIVE',
    ], 201);
} catch (Throwable $exception) {
    if ($pdo->inTransaction()) {
        $pdo->rollBack();
    }

    json_response([
        'error' => 'DATABASE_ERROR',
        'message' => 'Unable to hire candidate.',
    ], 500);
}
