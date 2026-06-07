#!/usr/bin/env python3
from pathlib import Path
import re

path = Path("api/lib/flight-dispatch-selection.php")
text = path.read_text(encoding="utf-8")

if "aircraft-type-rating.php" not in text:
    text = text.replace(
        "<?php\ndeclare(strict_types=1);",
        "<?php\ndeclare(strict_types=1);\n\nrequire_once __DIR__ . '/aircraft-type-rating.php';"
    )

new_function = r'''function dispatch_fetch_pilots_for_aircraft_model(PDO $pdo, int $companyId, string $modelCode): array
{
    $license = required_aircraft_type_rating($pdo, $modelCode);

    $sql = "
        SELECT s.id AS staff_id, s.display_name, s.salary_per_flight
        FROM company_staff s
        WHERE s.company_id = :company_id
          AND s.staff_role = 'PILOT'
          AND s.employment_status = 'ACTIVE'
          AND EXISTS (
            SELECT 1 FROM company_staff_licenses l
            WHERE l.company_staff_id = s.id AND l.license_code = 'CPL'
          )
    ";

    $params = ['company_id' => $companyId];

    if ($license !== null) {
        $sql .= "
          AND EXISTS (
            SELECT 1 FROM company_staff_licenses l
            WHERE l.company_staff_id = s.id AND l.license_code = :license
          )
        ";
        $params['license'] = $license;
    }

    $sql .= " ORDER BY s.reliability_score DESC, s.fatigue_score ASC, s.id LIMIT 2";

    $stmt = $pdo->prepare($sql);
    $stmt->execute($params);

    return $stmt->fetchAll();
}'''

text2 = re.sub(
    r"function dispatch_fetch_pilots_for_aircraft_model\(PDO \$pdo, int \$companyId, string \$modelCode\): array\s*\{.*?\n\}",
    new_function,
    text,
    count=1,
    flags=re.S,
)

if text2 == text:
    raise SystemExit("Could not replace dispatch_fetch_pilots_for_aircraft_model. Send me api/lib/flight-dispatch-selection.php")

path.write_text(text2, encoding="utf-8")
print("OK: dispatch now requires generic aircraft type rating, e.g. CONC_TYPE for Concorde.")
