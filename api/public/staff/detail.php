<?php
declare(strict_types=1);

require __DIR__ . '/../../lib/bootstrap.php';
require __DIR__ . '/../../lib/session.php';

$session = require_auth_session();
$companyId = (int)$session['company_id'];
$staffId = filter_input(INPUT_GET, 'staffId', FILTER_VALIDATE_INT);

if (!$staffId) {
    json_response(['error' => 'INVALID_STAFF_ID'], 422);
}

$pdo = db();

$stmt = $pdo->prepare("
    SELECT *
    FROM company_staff
    WHERE company_id = :company_id
      AND id = :staff_id
    LIMIT 1
");
$stmt->execute([
    'company_id' => $companyId,
    'staff_id' => $staffId,
]);
$staff = $stmt->fetch();

if (!$staff) {
    json_response(['error' => 'STAFF_NOT_FOUND'], 404);
}

$licenses = [];
if (table_exists($pdo, 'company_staff_licenses')) {
    $licenseStmt = $pdo->prepare("
        SELECT
          l.license_code,
          lt.name AS license_name
        FROM company_staff_licenses l
        LEFT JOIN staff_license_types lt
          ON lt.code = l.license_code
        WHERE l.company_staff_id = :staff_id
        ORDER BY l.license_code
    ");
    $licenseStmt->execute(['staff_id' => $staffId]);
    $licenses = $licenseStmt->fetchAll();
}

json_response([
    'staff' => $staff,
    'licenses' => $licenses,
]);

function table_exists(PDO $pdo, string $tableName): bool
{
    $stmt = $pdo->prepare("
        SELECT COUNT(*)
        FROM information_schema.TABLES
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = :table_name
    ");
    $stmt->execute(['table_name' => $tableName]);
    return (int)$stmt->fetchColumn() > 0;
}
