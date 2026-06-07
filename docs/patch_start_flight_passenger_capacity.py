#!/usr/bin/env python3
from pathlib import Path

path = Path("api/public/flights/start-service-now.php")
text = path.read_text(encoding="utf-8")

if "$capacity = max(1, (int)($aircraft['passenger_capacity_standard'] ?? 1));" not in text:
    raise SystemExit("Could not find capacity calculation. Send me api/public/flights/start-service-now.php")

if "put($values, $columns, 'passenger_capacity', $capacity);" not in text:
    text = text.replace(
        "put($values, $columns, 'passenger_count', $passengerCount);",
        "put($values, $columns, 'passenger_capacity', $capacity);\n    put($values, $columns, 'passenger_count', $passengerCount);"
    )

path.write_text(text, encoding="utf-8")
print("OK: start-service-now.php now sets passenger_capacity.")
