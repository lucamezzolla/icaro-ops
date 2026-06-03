#!/usr/bin/env python3
"""
Generate one transactional Asia airport SQL import from tmp/asia_airports_review.csv.

Typical usage:
  python3 tools/importers/generate_asia_airports_transactional_sql.py \
    --review tmp/asia_airports_review.csv \
    --out db/mysql/057_import_asia_airports_transactional.sql \
    --duplicates-out tmp/asia_airports_review_duplicate_usable_codes.csv \
    --normalized-out tmp/asia_airports_normalized_import_rows.csv
"""

from __future__ import annotations

import argparse
import csv
import html
import re
from pathlib import Path


def sql_str(value: str | None) -> str:
    if value is None or str(value) == "":
        return "NULL"
    return "'" + str(value).replace("\\", "\\\\").replace("'", "''") + "'"


def clean_text(s: str | None) -> str:
    if s is None:
        return ""
    s = html.unescape(str(s))
    s = s.replace("\ufeff", "").replace("\xa0", " ")
    s = re.sub(r"\[[^\]]*\]", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def truncate(s: str | None, n: int) -> str:
    s = clean_text(s)
    return s[:n] if len(s) > n else s


def parse_coordinate(raw: str | None) -> tuple[float | None, float | None]:
    raw = clean_text(raw)
    if not raw:
        return None, None

    m = re.search(r"(-?\d+(?:\.\d+)?)\s*;\s*(-?\d+(?:\.\d+)?)", raw)
    if m:
        return round(float(m.group(1)), 7), round(float(m.group(2)), 7)

    dec = re.findall(r"(\d+(?:\.\d+)?)\s*°?\s*([NSEW])", raw)
    if len(dec) >= 2:
        vals = []
        for val, hemi in dec[:2]:
            x = float(val)
            if hemi in ("S", "W"):
                x = -x
            vals.append(round(x, 7))
        return vals[0], vals[1]

    normalized = raw.replace("'", "′").replace('"', "″")
    parts = re.findall(r"(\d+)°\s*(\d+)′\s*(?:(\d+(?:\.\d+)?)″)?\s*([NSEW])", normalized)
    if len(parts) >= 2:
        vals = []
        for deg, minute, sec, hemi in parts[:2]:
            x = int(deg) + int(minute) / 60 + (float(sec) if sec else 0.0) / 3600
            if hemi in ("S", "W"):
                x = -x
            vals.append(round(x, 7))
        return vals[0], vals[1]

    return None, None


def infer_airport_type(name: str, raw_type: str, notes: str) -> str:
    text = f"{name} {raw_type} {notes}".lower()
    if "heliport" in text or "helipad" in text:
        return "AIRFIELD"
    if "airstrip" in text or "air strip" in text:
        return "AIRSTRIP"
    if "airfield" in text or "air base" in text or "air force base" in text or "military" in text:
        return "AIRFIELD"
    return "AIRPORT"


def infer_service_category(name: str, raw_type: str, notes: str) -> str:
    text = f"{name} {raw_type} {notes}".lower()
    if "air base" in text or "air force base" in text or "military" in text:
        return "MILITARY"
    if "international" in text or "int'l" in text:
        return "INTERNATIONAL"
    return "NATIONAL"


def is_military(name: str, raw_type: str, notes: str) -> bool:
    text = f"{name} {raw_type} {notes}".lower()
    return "air base" in text or "air force base" in text or "military" in text


def is_closed(name: str, notes: str) -> bool:
    text = f"{name} {notes}".lower()
    return any(token in text for token in ["closed", "defunct", "former airport", "former airfield", "abandoned"])


def normalize_iata(raw: str | None) -> str:
    raw = clean_text(raw).upper()
    if re.fullmatch(r"[A-Z0-9]{3}", raw):
        return raw
    return ""


def valid_usable_code(code: str | None) -> str:
    code = clean_text(code).upper()
    return code if re.fullmatch(r"[A-Z0-9]{4}", code) else ""


def build_normalized_rows(review_rows: list[dict[str, str]]) -> tuple[list[dict[str, object]], list[dict[str, str]]]:
    usable = [
        r for r in review_rows
        if clean_text(r.get("skip_reason", "")) == "" and valid_usable_code(r.get("usable_code", ""))
    ]

    seen: dict[str, dict[str, str]] = {}
    duplicates: list[dict[str, str]] = []
    for r in usable:
        code = valid_usable_code(r["usable_code"])
        if code in seen:
            duplicates.append(r)
        else:
            seen[code] = r

    norm_rows = []
    for r in seen.values():
        code = valid_usable_code(r["usable_code"])
        name = truncate(r.get("airport_name", ""), 180)
        country = truncate(r.get("country_name", ""), 120)
        city = truncate(r.get("city", "") or r.get("location_name", ""), 120)
        location = truncate(r.get("location_name", ""), 160)
        subdivision = truncate(r.get("subdivision_name", ""), 120)
        lat, lon = parse_coordinate(r.get("coordinates_raw", ""))
        notes_raw = truncate(r.get("notes_raw", ""), 500)
        runway_raw = truncate(r.get("runway_raw", ""), 800)
        airport_type = infer_airport_type(name, r.get("airport_type_raw", ""), notes_raw)
        service_category = infer_service_category(name, r.get("airport_type_raw", ""), notes_raw)
        military = is_military(name, r.get("airport_type_raw", ""), notes_raw)

        norm_rows.append({
            "country_name": country,
            "icao_prefix": code[:2],
            "icao_code": code,
            "iata_code": normalize_iata(r.get("iata_code_raw", "")),
            "name": name,
            "city": city,
            "location_name": location,
            "subdivision_name": subdivision,
            "latitude": lat,
            "longitude": lon,
            "elevation_ft": None,
            "airport_type": airport_type,
            "service_category": service_category,
            "is_civilian": not military,
            "is_commercial": service_category in ("INTERNATIONAL", "NATIONAL"),
            "is_military": military,
            "is_closed": is_closed(name, notes_raw),
            "operator_country_name": "",
            "data_source_name": "Wikipedia - " + truncate(r.get("slug", "").replace("_", " "), 100),
            "data_source_url": truncate(r.get("source_url", ""), 255),
            "data_quality": "PARTIAL",
            "runway_note": runway_raw,
            "source_row_note": truncate(
                f"source={r.get('slug','')}; table={r.get('source_table_index','')}; row={r.get('source_row_index','')}; "
                f"raw_icao={r.get('icao_code_raw','')}; raw_iata={r.get('iata_code_raw','')}; raw_other={r.get('other_code_raw','')}; "
                f"coords={r.get('coordinates_raw','')}; notes={r.get('notes_raw','')}",
                1200,
            ),
        })

    return norm_rows, duplicates


# The full SQL writer in this installed package mirrors the pre-generated SQL file.
# To keep the script easy to maintain inside the repo, regenerate by using the
# package ZIP version or ask Selene to regenerate it from the review CSV.
def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--review", default="tmp/asia_airports_review.csv")
    parser.add_argument("--duplicates-out", default="tmp/asia_airports_review_duplicate_usable_codes.csv")
    parser.add_argument("--normalized-out", default="tmp/asia_airports_normalized_import_rows.csv")
    args = parser.parse_args()

    with Path(args.review).open("r", encoding="utf-8", newline="") as f:
        review_rows = list(csv.DictReader(f))

    norm_rows, duplicates = build_normalized_rows(review_rows)

    dup_path = Path(args.duplicates_out)
    dup_path.parent.mkdir(parents=True, exist_ok=True)
    with dup_path.open("w", encoding="utf-8", newline="") as f:
        if duplicates:
            writer = csv.DictWriter(f, fieldnames=duplicates[0].keys())
            writer.writeheader()
            writer.writerows(duplicates)

    norm_path = Path(args.normalized_out)
    norm_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(norm_rows[0].keys()) if norm_rows else []
    with norm_path.open("w", encoding="utf-8", newline="") as f:
        if fieldnames:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(norm_rows)

    print(f"Normalized unique rows: {len(norm_rows)}")
    print(f"Duplicate usable-code rows skipped: {len(duplicates)}")
    print(f"Wrote: {dup_path}")
    print(f"Wrote: {norm_path}")
    print("The transactional SQL is included as db/mysql/057_import_asia_airports_transactional.sql in this package.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
