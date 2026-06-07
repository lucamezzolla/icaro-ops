#!/usr/bin/env python3
"""
Generate and optionally apply a MySQL migration that updates coordinates for
existing Icaro Ops airports using the OurAirports airports.csv dataset.

Default behavior:
  - reads existing ICAO codes from the local MySQL database through mysql CLI
  - downloads OurAirports airports.csv
  - writes db/mysql/117_update_airport_coordinates_from_ourairports.sql
  - does NOT apply unless --apply is passed

This script intentionally updates only existing rows in airports. It does not
insert thousands of new airports.
"""

from __future__ import annotations

import argparse
import csv
import io
import os
import subprocess
import sys
import textwrap
import urllib.request
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Dict, Iterable, Optional, Tuple

OURAIRPORTS_CSV_URL = "https://ourairports.com/airports.csv"
DEFAULT_DB = "icaro_ops"
OUTPUT_SQL = Path("db/mysql/117_update_airport_coordinates_from_ourairports.sql")
DOC_PATH = Path("docs/UPDATE_AIRPORT_COORDINATES_FROM_OURAIRPORTS.md")


def run_mysql_query(database: str, query: str, sudo: bool) -> str:
    command = []
    if sudo:
        command.append("sudo")
    command += ["mysql", "-N", "-B", database, "-e", query]
    result = subprocess.run(command, check=True, text=True, capture_output=True)
    return result.stdout


def get_existing_icao_codes(database: str, sudo: bool) -> set[str]:
    output = run_mysql_query(
        database,
        "SELECT UPPER(TRIM(icao_code)) FROM airports WHERE icao_code IS NOT NULL AND TRIM(icao_code) <> '';",
        sudo,
    )
    codes = {line.strip().upper() for line in output.splitlines() if line.strip()}
    return {code for code in codes if len(code) == 4}


def download_csv(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": "IcaroOpsCoordinateUpdater/1.0"})
    with urllib.request.urlopen(request, timeout=60) as response:
        encoding = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(encoding)


def parse_decimal(value: str) -> Optional[Decimal]:
    value = (value or "").strip()
    if not value:
        return None
    try:
        return Decimal(value)
    except InvalidOperation:
        return None


def parse_int(value: str) -> Optional[int]:
    value = (value or "").strip()
    if not value:
        return None
    try:
        return int(float(value))
    except ValueError:
        return None


def is_valid_coordinate(lat: Optional[Decimal], lon: Optional[Decimal]) -> bool:
    if lat is None or lon is None:
        return False
    return Decimal("-90") <= lat <= Decimal("90") and Decimal("-180") <= lon <= Decimal("180")


def sql_string(value: str) -> str:
    return "'" + value.replace("\\", "\\\\").replace("'", "''") + "'"


def sql_decimal(value: Decimal, places: int = 7) -> str:
    quantized = value.quantize(Decimal("1." + ("0" * places)))
    return format(quantized, "f")


def sql_nullable_int(value: Optional[int]) -> str:
    return "NULL" if value is None else str(value)


def build_coordinate_map(csv_text: str) -> Dict[str, Tuple[Decimal, Decimal, Optional[int], str]]:
    rows = csv.DictReader(io.StringIO(csv_text))
    by_code: Dict[str, Tuple[Decimal, Decimal, Optional[int], str]] = {}

    for row in rows:
        lat = parse_decimal(row.get("latitude_deg", ""))
        lon = parse_decimal(row.get("longitude_deg", ""))
        if not is_valid_coordinate(lat, lon):
            continue

        elevation = parse_int(row.get("elevation_ft", ""))
        airport_type = (row.get("type") or "").strip()

        candidates = []
        for field in ("gps_code", "ident"):
            code = (row.get(field) or "").strip().upper()
            if len(code) == 4 and code.isalnum():
                candidates.append(code)

        for code in candidates:
            # Prefer non-closed airport records when duplicated.
            existing = by_code.get(code)
            if existing is None or (existing[3] == "closed_airport" and airport_type != "closed_airport"):
                by_code[code] = (lat, lon, elevation, airport_type)

    return by_code


def write_sql(output_path: Path, matches: Dict[str, Tuple[Decimal, Decimal, Optional[int], str]]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    lines = [
        "-- Update airport coordinates from OurAirports.",
        f"-- Generated at: {generated_at}",
        "-- Source: https://ourairports.com/airports.csv",
        "-- Scope: update existing airports only; do not insert new airports.",
        "",
        "USE icaro_ops;",
        "",
        "START TRANSACTION;",
        "",
    ]

    for code in sorted(matches):
        lat, lon, elevation, airport_type = matches[code]
        lines.append(
            "UPDATE airports\n"
            f"SET latitude = {sql_decimal(lat)},\n"
            f"    longitude = {sql_decimal(lon)},\n"
            f"    elevation_ft = COALESCE(elevation_ft, {sql_nullable_int(elevation)}),\n"
            "    data_source_name = 'OurAirports',\n"
            "    data_source_url = 'https://ourairports.com/airports.csv',\n"
            "    data_quality = CASE WHEN data_quality = 'VERIFIED' THEN 'VERIFIED' ELSE 'PARTIAL' END,\n"
            "    verified_at_utc = UTC_TIMESTAMP()\n"
            f"WHERE icao_code = {sql_string(code)};\n"
        )

    lines += [
        "COMMIT;",
        "",
        "SELECT COUNT(*) AS airports_without_coordinates_remaining",
        "FROM airports",
        "WHERE latitude IS NULL OR longitude IS NULL;",
        "",
    ]

    output_path.write_text("\n".join(lines), encoding="utf-8")


def write_doc(doc_path: Path, matched_count: int, missing_count: int) -> None:
    doc_path.parent.mkdir(parents=True, exist_ok=True)
    doc_path.write_text(
        textwrap.dedent(
            f"""
            # Update airport coordinates from OurAirports

            This patch generates a local MySQL migration that updates latitude and longitude
            for airports already present in the Icaro Ops database.

            Source dataset: OurAirports `airports.csv`.

            Important rules:

            - Existing airports are updated by ICAO code.
            - The script does not insert thousands of new airports.
            - Existing `VERIFIED` quality is preserved.
            - Non-verified rows updated by this script are marked as `PARTIAL`.
            - Existing `elevation_ft` values are preserved; missing elevation is filled when available.

            Last generated summary:

            - Matched existing airports: {matched_count}
            - Existing airports not found in OurAirports by ICAO/gps code: {missing_count}

            Recommended commands:

            ```bash
            python3 tools/update_airport_coordinates_from_ourairports.py
            sudo mysql icaro_ops < db/mysql/117_update_airport_coordinates_from_ourairports.sql
            ```

            Verification:

            ```bash
            sudo mysql icaro_ops -e "
            SELECT COUNT(*) AS airports_without_coordinates_remaining
            FROM airports
            WHERE latitude IS NULL OR longitude IS NULL;
            "
            ```
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )


def apply_sql(database: str, sql_path: Path, sudo: bool) -> None:
    command = []
    if sudo:
        command.append("sudo")
    command += ["mysql", database]
    with sql_path.open("rb") as handle:
        subprocess.run(command, check=True, stdin=handle)


def main() -> int:
    parser = argparse.ArgumentParser(description="Update Icaro Ops airport coordinates from OurAirports.")
    parser.add_argument("--database", default=DEFAULT_DB, help="MySQL database name. Default: icaro_ops")
    parser.add_argument("--no-sudo", action="store_true", help="Run mysql without sudo.")
    parser.add_argument("--apply", action="store_true", help="Apply the generated SQL immediately.")
    parser.add_argument("--csv", default="", help="Use a local airports.csv instead of downloading it.")
    args = parser.parse_args()

    sudo = not args.no_sudo

    existing_codes = get_existing_icao_codes(args.database, sudo)
    if not existing_codes:
        print("No existing ICAO airports found in database.", file=sys.stderr)
        return 1

    if args.csv:
        csv_text = Path(args.csv).read_text(encoding="utf-8")
    else:
        csv_text = download_csv(OURAIRPORTS_CSV_URL)

    coordinate_map = build_coordinate_map(csv_text)
    matches = {code: coordinate_map[code] for code in existing_codes if code in coordinate_map}
    missing = sorted(existing_codes - set(matches))

    write_sql(OUTPUT_SQL, matches)
    write_doc(DOC_PATH, len(matches), len(missing))

    print(f"Existing ICAO airports in DB: {len(existing_codes)}")
    print(f"Coordinates matched: {len(matches)}")
    print(f"Not found in OurAirports by ICAO/gps code: {len(missing)}")
    print(f"Generated: {OUTPUT_SQL}")
    print(f"Generated: {DOC_PATH}")

    if missing[:20]:
        print("First missing ICAO codes: " + ", ".join(missing[:20]))

    if args.apply:
        apply_sql(args.database, OUTPUT_SQL, sudo)
        print("Applied SQL migration.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
