#!/usr/bin/env python3
from pathlib import Path
import re

for filename in ["api/public/routes/list.php", "api/public/routes/detail.php"]:
    path = Path(filename)
    text = path.read_text(encoding="utf-8")

    # Ensure flight_route_code is selected from scheduled_services.
    if "ss.flight_route_code" not in text:
        text = text.replace(
            "ss.service_code,",
            "ss.service_code,\n      ss.flight_route_code,",
            1
        )

    path.write_text(text, encoding="utf-8")
    print(f"OK: {filename} exposes flight_route_code.")
