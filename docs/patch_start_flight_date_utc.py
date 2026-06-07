#!/usr/bin/env python3
from pathlib import Path

path = Path("api/public/flights/start-service-now.php")
text = path.read_text(encoding="utf-8")

# Add a UTC date variable near the existing UTC timestamp setup.
if "$todayUtc = gmdate('Y-m-d');" not in text:
    text = text.replace(
        "$now = gmdate('Y-m-d H:i:s');\n    $arrival = gmdate('Y-m-d H:i:s', time() + ($durationMinutes * 60));",
        "$now = gmdate('Y-m-d H:i:s');\n    $todayUtc = gmdate('Y-m-d');\n    $arrival = gmdate('Y-m-d H:i:s', time() + ($durationMinutes * 60));"
    )

# Insert flight_date_utc if the DB table has the column.
if "put($values, $columns, 'flight_date_utc', $todayUtc);" not in text:
    text = text.replace(
        "put($values, $columns, 'flight_code', $flightCode);",
        "put($values, $columns, 'flight_code', $flightCode);\n    put($values, $columns, 'flight_date_utc', $todayUtc);"
    )

path.write_text(text, encoding="utf-8")
print("OK: start-service-now.php now sets flight_date_utc.")
