#!/usr/bin/env python3
from pathlib import Path

PROJECT = Path.cwd()
DASHBOARD_JS = PROJECT / "src/js/dashboard-map.js"

REPLACEMENTS = [
    ('"Aircraft"', '"Base managed aircraft"'),
    ('"At base"', '"On ground at current base"'),
    ('"Free fleet slots"', '"Free base fleet slots"'),
    ('"Free ground slots"', '"Free base ground slots"'),
    ('"In flight"', '"Company aircraft in flight"'),
    ('"Maintenance"', '"Company aircraft in maintenance"'),

    ('''firstDefined(
      capacity.aircraft_in_flight_count,
      data.aircraft_in_flight_count
    )''', '''firstDefined(
      data.aircraft_in_flight_count,
      capacity.aircraft_in_flight_count
    )'''),

    ('''firstDefined(
      capacity.aircraft_maintenance_count,
      data.aircraft_maintenance_count
    )''', '''firstDefined(
      data.aircraft_maintenance_count,
      capacity.aircraft_maintenance_count
    )'''),
]

def main() -> None:
    if not DASHBOARD_JS.exists():
        raise FileNotFoundError(f"Missing file: {DASHBOARD_JS}")

    content = DASHBOARD_JS.read_text(encoding="utf-8")
    original = content

    for old, new in REPLACEMENTS:
        content = content.replace(old, new)

    if content == original:
        raise RuntimeError("No dashboard labels were changed. The file may already be patched or has changed.")

    DASHBOARD_JS.write_text(content, encoding="utf-8")
    print("Patched dashboard-map.js: clarified company/global vs current-base capacity labels.")

if __name__ == "__main__":
    main()
