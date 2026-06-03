#!/usr/bin/env python3
"""
Download linked Wikipedia airport-list pages and produce a lightweight table probe.

Input:
  tmp/wiki_airport_lists_asia.csv

Output:
  tmp/wiki_airport_lists_asia_probe.csv

This does not parse airport rows yet. It helps us understand how many wikitable
sections each page has before generating SQL.
"""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path
from urllib.request import Request, urlopen


USER_AGENT = "IcaroOpsAirportImporter/0.1 (local development; contact: project owner)"


def fetch_html(url: str) -> str:
    req = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(req, timeout=30) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, errors="replace")


def count_wikitables(html: str) -> int:
    return len(re.findall(r'<table[^>]+class="[^"]*\bwikitable\b', html, flags=re.I))


def has_airport_headers(html: str) -> bool:
    compact = re.sub(r"\s+", " ", html).lower()
    expected = ["icao", "iata", "airport", "location"]
    return any(word in compact for word in expected)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--in", dest="input_csv", default="tmp/wiki_airport_lists_asia.csv")
    parser.add_argument("--out", dest="output_csv", default="tmp/wiki_airport_lists_asia_probe.csv")
    args = parser.parse_args()

    input_path = Path(args.input_csv)
    output_path = Path(args.output_csv)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with input_path.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))

    out_rows = []
    for row in rows:
        url = row["url"]
        try:
            html = fetch_html(url)
            out_rows.append({
                "label": row["label"],
                "slug": row["slug"],
                "url": url,
                "wikitable_count": count_wikitables(html),
                "has_airport_like_headers": "yes" if has_airport_headers(html) else "no",
                "status": "ok",
                "error": "",
            })
            print(f"OK {row['label']}: {url}")
        except Exception as exc:
            out_rows.append({
                "label": row["label"],
                "slug": row["slug"],
                "url": url,
                "wikitable_count": "",
                "has_airport_like_headers": "",
                "status": "error",
                "error": str(exc),
            })
            print(f"ERROR {row['label']}: {exc}")

    with output_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "label",
                "slug",
                "url",
                "wikitable_count",
                "has_airport_like_headers",
                "status",
                "error",
            ],
        )
        writer.writeheader()
        writer.writerows(out_rows)

    print(f"Wrote: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
