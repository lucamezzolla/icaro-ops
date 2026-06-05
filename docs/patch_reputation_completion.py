#!/usr/bin/env python3
from pathlib import Path

files_to_patch = [
    Path("api/public/flights/active.php"),
    Path("api/public/flights/start-scheduled.php"),
    Path("api/public/dispatch/process-due-routes.php"),
]

for path in files_to_patch:
    if not path.exists():
        print(f"SKIP missing {path}")
        continue

    text = path.read_text(encoding="utf-8")

    if "lib/reputation.php" not in text:
        text = text.replace(
            "require __DIR__ . '/../../lib/session.php';",
            "require __DIR__ . '/../../lib/session.php';\nrequire __DIR__ . '/../../lib/reputation.php';",
            1
        )

    needle = """)->execute([
            'profit' => (float)$flight['profit_amount'],
            'company_id' => $companyId,
        ]);"""

    insert = """)->execute([
            'profit' => (float)$flight['profit_amount'],
            'company_id' => $companyId,
        ]);

        $profit = (float)$flight['profit_amount'];

        apply_reputation_event(
            $pdo,
            $companyId,
            $profit > 0 ? 'FLIGHT_COMPLETED_PROFITABLE' : 'FLIGHT_COMPLETED_BREAK_EVEN_OR_LOSS',
            'FLIGHT',
            (int)$flight['id'],
            $profit > 0
                ? 'Flight completed successfully with positive profit.'
                : 'Flight completed successfully but did not generate positive profit.'
        );"""

    if "FLIGHT_COMPLETED_PROFITABLE" not in text and needle in text:
        text = text.replace(needle, insert)

    path.write_text(text, encoding="utf-8")
    print(f"OK patched {path}")

print("Review with: git diff")
