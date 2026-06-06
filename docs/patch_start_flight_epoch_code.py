#!/usr/bin/env python3
from pathlib import Path
import re

path = Path("api/public/flights/start-service-now.php")
text = path.read_text(encoding="utf-8")

new_fn = r'''function next_flight_code(PDO $pdo, int $companyId): string {
    $base = time();
    $code = 'IO-' . $base;

    $stmt = $pdo->prepare("
        SELECT COUNT(*)
        FROM scheduled_flight_instances
        WHERE company_id = :company_id
          AND flight_code = :flight_code
    ");

    $suffix = 0;

    while (true) {
        $candidate = $suffix === 0 ? $code : $code . '-' . $suffix;
        $stmt->execute([
            'company_id' => $companyId,
            'flight_code' => $candidate,
        ]);

        if ((int)$stmt->fetchColumn() === 0) {
            return $candidate;
        }

        $suffix++;
    }
}'''

if "function next_flight_code(" not in text:
    raise SystemExit("next_flight_code function not found in api/public/flights/start-service-now.php")

text = re.sub(
    r"function next_flight_code\(PDO \$pdo, int \$companyId\): string\s*\{.*?\n\}",
    new_fn,
    text,
    count=1,
    flags=re.S
)

path.write_text(text, encoding="utf-8")
print("OK: flight instance code is now IO-<epoch>.")
