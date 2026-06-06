<?php
declare(strict_types=1);

require __DIR__ . '/../../lib/bootstrap.php';
require __DIR__ . '/../../lib/session.php';

require_auth_session();

$candidateId = filter_input(INPUT_GET, 'id', FILTER_VALIDATE_INT);

if (!$candidateId) {
    json_response(['error' => 'INVALID_CANDIDATE_ID'], 422);
}

$pdo = db();

$stmt = $pdo->prepare("
    SELECT *
    FROM staff_candidates
    WHERE id = :id
    LIMIT 1
");
$stmt->execute(['id' => $candidateId]);
$candidate = $stmt->fetch();

if (!$candidate) {
    json_response(['error' => 'CANDIDATE_NOT_FOUND'], 404);
}

$licensesStmt = $pdo->prepare("
    SELECT
      license_code,
      proficiency_score,
      issued_at_utc,
      expires_at_utc
    FROM staff_candidate_licenses
    WHERE candidate_id = :id
    ORDER BY license_code
");
$licensesStmt->execute(['id' => $candidateId]);

json_response([
    'candidate' => $candidate,
    'licenses' => $licensesStmt->fetchAll(),
]);
