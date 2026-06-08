#!/usr/bin/env python3
from pathlib import Path

PROJECT = Path.cwd()

STAFF_LIST = PROJECT / "api/public/staff/list.php"
STAFF_MY = PROJECT / "api/public/staff/my-staff.php"
STAFF_JS = PROJECT / "src/js/staff.js"
SQL_PATCH = PROJECT / "db/mysql/patch_staff_operational_status.sql"

STAFF_ENDPOINT_CONTENT = '<?php\ndeclare(strict_types=1);\n\nrequire __DIR__ . \'/../../lib/bootstrap.php\';\nrequire __DIR__ . \'/../../lib/session.php\';\n\n$session = require_auth_session();\n$companyId = (int)$session[\'company_id\'];\n$pdo = db();\n\n$crewColumns = existing_columns($pdo, \'scheduled_flight_instances\', [\n    \'pilot_1_staff_id\',\n    \'pilot_2_staff_id\',\n    \'technician_staff_id\',\n]);\n\n$busyCondition = \'0 = 1\';\n\nif ($crewColumns !== []) {\n    $checks = array_map(\n        static fn (string $column): string => "f.`{$column}` = s.company_staff_id",\n        $crewColumns\n    );\n\n    $busyCondition = implode(\' OR \', $checks);\n}\n\n$sql = "\n    SELECT\n      s.*,\n      CASE\n        WHEN EXISTS (\n          SELECT 1\n          FROM scheduled_flight_instances f\n          WHERE f.company_id = s.company_id\n            AND f.status = \'IN_FLIGHT\'\n            AND ({$busyCondition})\n        )\n        THEN \'IN_FLIGHT\'\n        ELSE \'AVAILABLE\'\n      END AS operational_status\n    FROM v_company_staff s\n    WHERE s.company_id = :company_id\n      AND s.employment_status <> \'DISMISSED\'\n    ORDER BY s.staff_role, s.display_name\n";\n\n$stmt = $pdo->prepare($sql);\n$stmt->execute([\'company_id\' => $companyId]);\n\njson_response(array_map(static function (array $row): array {\n    return [\n        \'company_staff_id\' => (int)$row[\'company_staff_id\'],\n        \'company_id\' => (int)$row[\'company_id\'],\n        \'display_name\' => $row[\'display_name\'],\n        \'staff_role\' => $row[\'staff_role\'],\n        \'employment_status\' => $row[\'employment_status\'],\n        \'operational_status\' => $row[\'operational_status\'] ?? \'AVAILABLE\',\n        \'assigned_base_icao_code\' => $row[\'assigned_base_icao_code\'],\n        \'age_years\' => (int)$row[\'age_years\'],\n        \'experience_level\' => $row[\'experience_level\'],\n        \'fear_score\' => (int)$row[\'fear_score\'],\n        \'courage_score\' => (int)$row[\'courage_score\'],\n        \'stress_tolerance_score\' => (int)$row[\'stress_tolerance_score\'],\n        \'discipline_score\' => (int)$row[\'discipline_score\'],\n        \'teamwork_score\' => (int)$row[\'teamwork_score\'],\n        \'reliability_score\' => (int)$row[\'reliability_score\'],\n        \'ambition_score\' => (int)$row[\'ambition_score\'],\n        \'fatigue_risk_score\' => (int)$row[\'fatigue_risk_score\'],\n        \'flight_hours_total\' => (int)$row[\'flight_hours_total\'],\n        \'aircraft_maintenance_hours_total\' => (int)$row[\'aircraft_maintenance_hours_total\'],\n        \'salary_per_flight\' => $row[\'salary_per_flight\'],\n        \'daily_retainer\' => $row[\'daily_retainer\'],\n        \'revenue_share_percent\' => $row[\'revenue_share_percent\'],\n        \'currency_code\' => $row[\'currency_code\'],\n        \'morale_score\' => (int)$row[\'morale_score\'],\n        \'fatigue_score\' => (int)$row[\'fatigue_score\'],\n        \'licenses_summary\' => $row[\'licenses_summary\'] ?? \'\',\n    ];\n}, $stmt->fetchAll()));\n\nfunction existing_columns(PDO $pdo, string $tableName, array $candidateColumns): array\n{\n    if ($candidateColumns === []) {\n        return [];\n    }\n\n    $placeholders = implode(\', \', array_fill(0, count($candidateColumns), \'?\'));\n    $stmt = $pdo->prepare("\n        SELECT COLUMN_NAME\n        FROM information_schema.COLUMNS\n        WHERE TABLE_SCHEMA = DATABASE()\n          AND TABLE_NAME = ?\n          AND COLUMN_NAME IN ({$placeholders})\n    ");\n\n    $stmt->execute(array_merge([$tableName], $candidateColumns));\n\n    return array_map(static fn (array $row): string => $row[\'COLUMN_NAME\'], $stmt->fetchAll());\n}\n'
SQL_CONTENT = 'ALTER TABLE scheduled_flight_instances\n  ADD COLUMN IF NOT EXISTS pilot_1_staff_id BIGINT(20) UNSIGNED NULL AFTER dispatch_aircraft_id,\n  ADD COLUMN IF NOT EXISTS pilot_2_staff_id BIGINT(20) UNSIGNED NULL AFTER pilot_1_staff_id,\n  ADD COLUMN IF NOT EXISTS technician_staff_id BIGINT(20) UNSIGNED NULL AFTER pilot_2_staff_id;\n\nCREATE INDEX IF NOT EXISTS idx_sfi_pilot_1_staff_status\n  ON scheduled_flight_instances (pilot_1_staff_id, status);\n\nCREATE INDEX IF NOT EXISTS idx_sfi_pilot_2_staff_status\n  ON scheduled_flight_instances (pilot_2_staff_id, status);\n\nCREATE INDEX IF NOT EXISTS idx_sfi_technician_staff_status\n  ON scheduled_flight_instances (technician_staff_id, status);\n'

def read(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path}")
    return path.read_text(encoding="utf-8")

def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")

def patch_staff_js() -> None:
    js = read(STAFF_JS)

    old_status_cell = '<td><span class="badge ${s.employment_status === "ACTIVE" ? "good" : "warn"}">${escapeHtml(s.employment_status || "-")}</span></td>'
    new_status_cell = '<td>${staffStatusBadges(s)}</td>'

    if old_status_cell in js:
        js = js.replace(old_status_cell, new_status_cell, 1)
    elif "staffStatusBadges(s)" not in js:
        raise RuntimeError("Could not find Staff status table cell in src/js/staff.js")

    if "function staffStatusBadges(" not in js:
        helper = r"""
function staffStatusBadges(s) {
  const employmentStatus = s.employment_status || "-";
  const operationalStatus = s.operational_status || "AVAILABLE";
  const employmentClass = employmentStatus === "ACTIVE" ? "good" : "warn";
  const operationalClass = operationalStatus === "AVAILABLE" ? "good" : "warn";
  const operationalLabel = operationalStatus === "IN_FLIGHT" ? "IN FLIGHT / BUSY" : operationalStatus;

  return `
    <span class="badge ${employmentClass}">${escapeHtml(employmentStatus)}</span>
    <span class="badge ${operationalClass}">${escapeHtml(operationalLabel)}</span>
  `;
}
"""
        marker = "\nfunction staffCostProfile("
        if marker in js:
            js = js.replace(marker, helper + marker, 1)
        else:
            js += "\n" + helper

    old_detail_status = '["Status", staff.employment_status],'
    new_detail_status = '["Employment status", staff.employment_status],\n          ["Operational status", staff.operational_status || "AVAILABLE"],'

    if old_detail_status in js:
        js = js.replace(old_detail_status, new_detail_status, 1)

    write(STAFF_JS, js)

def main() -> None:
    write(STAFF_LIST, STAFF_ENDPOINT_CONTENT)
    write(STAFF_MY, STAFF_ENDPOINT_CONTENT)
    write(SQL_PATCH, SQL_CONTENT)
    patch_staff_js()

    print("Patched staff operational status.")
    print("Next step: apply db/mysql/patch_staff_operational_status.sql to your database.")

if __name__ == "__main__":
    main()
