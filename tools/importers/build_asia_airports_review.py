#!/usr/bin/env python3
"""
Build a review CSV from Wikipedia airport-list pages.

Input:
  tmp/wiki_airport_lists_asia.csv

Output:
  tmp/asia_airports_review.csv

This script does NOT write SQL.
It produces a review file so we can inspect parsed rows before creating
one transactional SQL import file.

Design goals:
- stdlib only: no pandas, no BeautifulSoup required
- robust enough for Wikipedia wikitable pages
- conservative normalization
"""

from __future__ import annotations

import argparse
import csv
import html
import re
import sys
import time
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path
from urllib.request import Request, urlopen


USER_AGENT = "IcaroOpsAirportImporter/0.2 (local development; review-only parser)"


DEFAULT_EXCLUDE_SLUGS = {
    # Already handled separately or not Asia for this import pass.
    "List_of_airports_in_Antarctica",
    "List_of_airports_in_Egypt",

    # Duplicates / political duplicates likely covered by another link in the same index.
    # Keep this conservative; we can re-enable manually later if needed.
    "List_of_airports_in_Palestine",
}


def fetch_html(url: str) -> str:
    req = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(req, timeout=45) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, errors="replace")


def clean_cell_text(value: str) -> str:
    value = html.unescape(value)
    value = re.sub(r"\[[^\]]*\]", "", value)          # remove [1], [note 1]
    value = re.sub(r"\s+", " ", value)
    value = value.replace("\xa0", " ").strip()
    return value


def wiki_label_to_country(label: str, slug: str) -> str:
    label = clean_cell_text(label)
    if label.startswith("List of airports in the "):
        return label.removeprefix("List of airports in the ").strip()
    if label.startswith("List of airports in "):
        return label.removeprefix("List of airports in ").strip()
    if label:
        return label.strip()

    slug_name = slug.removeprefix("List_of_airports_in_the_").removeprefix("List_of_airports_in_")
    return slug_name.replace("_", " ").strip()


@dataclass
class TableCell:
    tag: str
    text: str


@dataclass
class TableData:
    table_index: int
    rows: list[list[TableCell]] = field(default_factory=list)


class WikiTableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.tables: list[TableData] = []

        self._in_wikitable = False
        self._table_depth = 0
        self._current_table: TableData | None = None

        self._in_row = False
        self._current_row: list[TableCell] = []

        self._in_cell = False
        self._current_cell_tag = ""
        self._current_cell_parts: list[str] = []
        self._cell_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag_l = tag.lower()
        attrs_dict = dict(attrs)
        class_attr = attrs_dict.get("class", "") or ""

        if tag_l == "table":
            if self._in_wikitable:
                self._table_depth += 1
            elif "wikitable" in class_attr.split():
                self._in_wikitable = True
                self._table_depth = 1
                self._current_table = TableData(table_index=len(self.tables) + 1)

        if not self._in_wikitable:
            return

        if tag_l == "tr" and self._table_depth == 1:
            self._in_row = True
            self._current_row = []

        if tag_l in ("td", "th") and self._in_row and self._table_depth == 1:
            self._in_cell = True
            self._current_cell_tag = tag_l
            self._current_cell_parts = []
            self._cell_depth = 1
        elif self._in_cell:
            self._cell_depth += 1

        if self._in_cell and tag_l == "br":
            self._current_cell_parts.append(" | ")

    def handle_endtag(self, tag: str) -> None:
        tag_l = tag.lower()

        if not self._in_wikitable:
            return

        if self._in_cell:
            if tag_l in ("td", "th") and self._cell_depth <= 1:
                text = clean_cell_text("".join(self._current_cell_parts))
                self._current_row.append(TableCell(tag=self._current_cell_tag, text=text))
                self._in_cell = False
                self._current_cell_parts = []
                self._current_cell_tag = ""
                self._cell_depth = 0
            else:
                self._cell_depth -= 1
                if self._cell_depth < 1:
                    self._cell_depth = 1

        if tag_l == "tr" and self._in_row and self._table_depth == 1:
            if self._current_row and self._current_table:
                self._current_table.rows.append(self._current_row)
            self._in_row = False
            self._current_row = []

        if tag_l == "table":
            self._table_depth -= 1
            if self._table_depth <= 0:
                if self._current_table:
                    self.tables.append(self._current_table)
                self._in_wikitable = False
                self._current_table = None
                self._table_depth = 0

    def handle_data(self, data: str) -> None:
        if self._in_cell:
            self._current_cell_parts.append(data)


def canonical_header(header: str) -> str:
    h = clean_cell_text(header).casefold()
    h = h.replace("/", " ")
    h = re.sub(r"[^a-z0-9]+", "_", h).strip("_")

    if h in {"icao", "icao_code", "icao_airport_code"}:
        return "icao_code"
    if h in {"iata", "iata_code"}:
        return "iata_code"
    if "airport" in h and "name" in h:
        return "airport_name"
    if h in {"airport", "name"}:
        return "airport_name"
    if h in {"city", "town", "municipality"}:
        return "city"
    if "location" in h or "served" in h:
        return "location"
    if "region" in h or "province" in h or "state" in h or "prefecture" in h or "division" in h:
        return "subdivision"
    if "coordinates" in h or h == "coord":
        return "coordinates"
    if "runway" in h:
        return "runway"
    if "elevation" in h:
        return "elevation"
    if h in {"type", "airport_type"}:
        return "airport_type"
    if "notes" in h or "remarks" in h:
        return "notes"
    if "other" in h and "code" in h:
        return "other_code"

    return h or "unknown"


def table_to_dict_rows(table: TableData) -> tuple[list[str], list[dict[str, str]]]:
    if not table.rows:
        return [], []

    # Find the first row with TH cells as header.
    header_idx = None
    for i, row in enumerate(table.rows[:5]):
        if any(cell.tag == "th" for cell in row) and len(row) >= 2:
            header_idx = i
            break

    if header_idx is None:
        return [], []

    headers_raw = [cell.text for cell in table.rows[header_idx]]
    headers = [canonical_header(h) for h in headers_raw]

    out_rows: list[dict[str, str]] = []
    for row in table.rows[header_idx + 1:]:
        if len(row) < 2:
            continue

        values = [cell.text for cell in row]
        # Pad or trim to header length.
        if len(values) < len(headers):
            values = values + [""] * (len(headers) - len(values))
        values = values[:len(headers)]

        row_dict = {}
        for header, value in zip(headers, values):
            if header in row_dict and row_dict[header]:
                row_dict[header] += " | " + value
            else:
                row_dict[header] = value

        out_rows.append(row_dict)

    return headers, out_rows


def row_best_value(row: dict[str, str], keys: list[str]) -> str:
    for key in keys:
        value = row.get(key, "")
        if value:
            return value
    return ""


def normalize_review_row(country: str, slug: str, source_url: str, table_index: int, row_index: int, row: dict[str, str]) -> dict[str, str]:
    icao = row_best_value(row, ["icao_code", "icao", "icao_airport_code"]).strip()
    iata = row_best_value(row, ["iata_code", "iata"]).strip()
    other_code = row_best_value(row, ["other_code"]).strip()

    name = row_best_value(row, ["airport_name", "airport", "name"]).strip()
    city = row_best_value(row, ["city", "location"]).strip()
    location = row_best_value(row, ["location"]).strip()
    subdivision = row_best_value(row, ["subdivision", "region", "province", "state"]).strip()
    coordinates = row_best_value(row, ["coordinates"]).strip()
    runway = row_best_value(row, ["runway"]).strip()
    elevation = row_best_value(row, ["elevation"]).strip()
    airport_type = row_best_value(row, ["airport_type", "type"]).strip()
    notes = row_best_value(row, ["notes"]).strip()

    usable_code = ""
    code_source = ""
    if re.fullmatch(r"[A-Z0-9]{4}", icao):
        usable_code = icao
        code_source = "icao"
    elif re.fullmatch(r"[A-Z0-9]{4}", other_code):
        usable_code = other_code
        code_source = "other_code"

    skip_reason = ""
    if not name:
        skip_reason = "missing_airport_name"
    elif not usable_code:
        skip_reason = "missing_usable_4_char_code"

    return {
        "country_name": country,
        "slug": slug,
        "source_url": source_url,
        "source_table_index": str(table_index),
        "source_row_index": str(row_index),
        "usable_code": usable_code,
        "code_source": code_source,
        "icao_code_raw": icao,
        "iata_code_raw": iata,
        "other_code_raw": other_code,
        "airport_name": name,
        "city": city,
        "location_name": location,
        "subdivision_name": subdivision,
        "coordinates_raw": coordinates,
        "runway_raw": runway,
        "elevation_raw": elevation,
        "airport_type_raw": airport_type,
        "notes_raw": notes,
        "skip_reason": skip_reason,
    }


def should_exclude(slug: str, label: str, extra_excludes: set[str]) -> bool:
    if slug in DEFAULT_EXCLUDE_SLUGS:
        return True
    if slug in extra_excludes:
        return True
    return False


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--links", default="tmp/wiki_airport_lists_asia.csv")
    parser.add_argument("--out", default="tmp/asia_airports_review.csv")
    parser.add_argument("--include-excluded", action="store_true")
    parser.add_argument("--exclude-slug", action="append", default=[])
    parser.add_argument("--sleep", type=float, default=0.5)
    args = parser.parse_args()

    links_path = Path(args.links)
    output_path = Path(args.out)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with links_path.open("r", encoding="utf-8", newline="") as f:
        link_rows = list(csv.DictReader(f))

    extra_excludes = set(args.exclude_slug)
    review_rows: list[dict[str, str]] = []
    page_summaries: list[dict[str, str]] = []

    for link in link_rows:
        label = link["label"]
        slug = link["slug"]
        source_url = link["url"]
        country = wiki_label_to_country(label, slug)

        if not args.include_excluded and should_exclude(slug, label, extra_excludes):
            page_summaries.append({
                "country_name": country,
                "slug": slug,
                "source_url": source_url,
                "status": "excluded",
                "tables": "0",
                "parsed_rows": "0",
                "usable_rows": "0",
                "skipped_rows": "0",
                "error": "",
            })
            print(f"EXCLUDED {country}: {source_url}")
            continue

        try:
            html_text = fetch_html(source_url)
            table_parser = WikiTableParser()
            table_parser.feed(html_text)

            parsed_for_page = 0
            usable_for_page = 0
            skipped_for_page = 0

            for table in table_parser.tables:
                headers, dict_rows = table_to_dict_rows(table)
                # Skip tables that clearly are not airport data.
                if not headers:
                    continue
                if not any(h in headers for h in ("airport_name", "icao_code", "iata_code", "location", "city")):
                    continue

                for idx, row in enumerate(dict_rows, start=1):
                    norm = normalize_review_row(country, slug, source_url, table.table_index, idx, row)
                    parsed_for_page += 1
                    if norm["skip_reason"]:
                        skipped_for_page += 1
                    else:
                        usable_for_page += 1
                    review_rows.append(norm)

            page_summaries.append({
                "country_name": country,
                "slug": slug,
                "source_url": source_url,
                "status": "ok",
                "tables": str(len(table_parser.tables)),
                "parsed_rows": str(parsed_for_page),
                "usable_rows": str(usable_for_page),
                "skipped_rows": str(skipped_for_page),
                "error": "",
            })
            print(f"OK {country}: parsed={parsed_for_page}, usable={usable_for_page}, skipped={skipped_for_page}")

        except Exception as exc:
            page_summaries.append({
                "country_name": country,
                "slug": slug,
                "source_url": source_url,
                "status": "error",
                "tables": "",
                "parsed_rows": "0",
                "usable_rows": "0",
                "skipped_rows": "0",
                "error": str(exc),
            })
            print(f"ERROR {country}: {exc}", file=sys.stderr)

        if args.sleep > 0:
            time.sleep(args.sleep)

    fieldnames = [
        "country_name",
        "slug",
        "source_url",
        "source_table_index",
        "source_row_index",
        "usable_code",
        "code_source",
        "icao_code_raw",
        "iata_code_raw",
        "other_code_raw",
        "airport_name",
        "city",
        "location_name",
        "subdivision_name",
        "coordinates_raw",
        "runway_raw",
        "elevation_raw",
        "airport_type_raw",
        "notes_raw",
        "skip_reason",
    ]

    with output_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(review_rows)

    summary_path = output_path.with_name(output_path.stem + "_summary.csv")
    with summary_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "country_name",
                "slug",
                "source_url",
                "status",
                "tables",
                "parsed_rows",
                "usable_rows",
                "skipped_rows",
                "error",
            ],
        )
        writer.writeheader()
        writer.writerows(page_summaries)

    total = len(review_rows)
    usable = sum(1 for r in review_rows if not r["skip_reason"])
    skipped = total - usable

    print("")
    print(f"Wrote review: {output_path}")
    print(f"Wrote summary: {summary_path}")
    print(f"Review rows: {total}")
    print(f"Usable rows: {usable}")
    print(f"Skipped rows: {skipped}")
    print("")
    print("Next step: inspect the CSV files before generating SQL.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
