#!/usr/bin/env python3
from pathlib import Path

PROJECT = Path.cwd()
COMPANY_CURRENT = PROJECT / "api/public/company/current.php"

OLD = """      COALESCE(ps.aircraft_in_flight_count, 0) AS aircraft_in_flight_count,"""

NEW = """      (
        SELECT COUNT(*)
        FROM company_aircraft ca_in_flight
        WHERE ca_in_flight.company_id = co.id
          AND ca_in_flight.status = 'IN_FLIGHT'
      ) AS aircraft_in_flight_count,"""

def main() -> None:
    if not COMPANY_CURRENT.exists():
        raise FileNotFoundError(f"Missing file: {COMPANY_CURRENT}")

    content = COMPANY_CURRENT.read_text(encoding="utf-8")

    if NEW in content:
        print("Company in-flight count patch already applied.")
        return

    if OLD not in content:
        raise RuntimeError("Could not find the old aircraft_in_flight_count expression in api/public/company/current.php")

    content = content.replace(OLD, NEW, 1)
    COMPANY_CURRENT.write_text(content, encoding="utf-8")

    print("Patched company/current.php: company panel now counts all company aircraft with status IN_FLIGHT.")

if __name__ == "__main__":
    main()
