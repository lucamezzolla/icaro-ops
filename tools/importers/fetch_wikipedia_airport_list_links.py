#!/usr/bin/env python3
"""
Fetch airport-list links from a Wikipedia regional index page.

Default target:
  https://en.wikipedia.org/wiki/Lists_of_airports_in_Asia

This script intentionally does NOT generate SQL yet.
It creates a review CSV so we can verify the country/list URLs first.

Usage:
  python3 tools/importers/fetch_wikipedia_airport_list_links.py \
    --out tmp/wiki_airport_lists_asia.csv
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable
from urllib.parse import urljoin, urlparse, unquote
from urllib.request import Request, urlopen


DEFAULT_INDEX_URL = "https://en.wikipedia.org/wiki/Lists_of_airports_in_Asia"
USER_AGENT = "IcaroOpsAirportImporter/0.1 (local development; contact: project owner)"


@dataclass(frozen=True)
class Link:
    text: str
    href: str


class AnchorParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[Link] = []
        self._current_href: str | None = None
        self._current_text_parts: list[str] = []
        self._capture_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = dict(attrs)
        if tag.lower() == "a":
            href = attrs_dict.get("href")
            if href:
                self._current_href = href
                self._current_text_parts = []
                self._capture_depth = 1
        elif self._current_href:
            self._capture_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if self._current_href:
            self._capture_depth -= 1
            if tag.lower() == "a" or self._capture_depth <= 0:
                text = " ".join("".join(self._current_text_parts).split())
                self.links.append(Link(text=text, href=self._current_href))
                self._current_href = None
                self._current_text_parts = []
                self._capture_depth = 0

    def handle_data(self, data: str) -> None:
        if self._current_href:
            self._current_text_parts.append(data)


def fetch_html(url: str) -> str:
    req = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(req, timeout=30) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, errors="replace")


def is_airport_list_url(url: str, text: str) -> bool:
    parsed = urlparse(url)
    path = unquote(parsed.path)

    if not path.startswith("/wiki/"):
        return False

    # Keep only normal article pages.
    if ":" in path.removeprefix("/wiki/"):
        return False

    # Main expected pattern:
    # /wiki/List_of_airports_in_Afghanistan
    # /wiki/List_of_airports_in_Armenia
    # Some pages may be plural or have country-specific suffixes.
    slug = path.removeprefix("/wiki/")
    lower_slug = slug.lower()
    lower_text = text.lower()

    if lower_slug.startswith("list_of_airports_in_"):
        return True

    if "list of airports in" in lower_text:
        return True

    return False


def extract_airport_list_links(index_url: str) -> list[dict[str, str]]:
    html = fetch_html(index_url)
    parser = AnchorParser()
    parser.feed(html)

    seen_urls: set[str] = set()
    rows: list[dict[str, str]] = []

    for link in parser.links:
        absolute_url = urljoin(index_url, link.href)
        parsed = urlparse(absolute_url)

        # Normalize by removing fragments.
        absolute_url = parsed._replace(fragment="").geturl()

        if not is_airport_list_url(parsed.path, link.text):
            continue

        if absolute_url in seen_urls:
            continue
        seen_urls.add(absolute_url)

        slug = unquote(urlparse(absolute_url).path.removeprefix("/wiki/"))
        label = link.text.strip() or slug.replace("_", " ")

        rows.append({
            "label": label,
            "slug": slug,
            "url": absolute_url,
        })

    rows.sort(key=lambda r: r["label"].casefold())
    return rows


def write_csv(rows: Iterable[dict[str, str]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["label", "slug", "url"])
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--index-url", default=DEFAULT_INDEX_URL)
    parser.add_argument("--out", default="tmp/wiki_airport_lists_asia.csv")
    args = parser.parse_args()

    out = Path(args.out)
    rows = extract_airport_list_links(args.index_url)
    write_csv(rows, out)

    print(f"Index URL: {args.index_url}")
    print(f"Links found: {len(rows)}")
    print(f"Wrote: {out}")

    if not rows:
        print("WARNING: no airport-list links found.", file=sys.stderr)
        return 2

    for row in rows:
        print(f"- {row['label']}: {row['url']}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
