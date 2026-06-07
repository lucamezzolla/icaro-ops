#!/usr/bin/env python3
from pathlib import Path
import re

def remove_market_explanations(text: str) -> str:
    patterns = [
        r"\s*<[^>]*>\s*Pilot coverage rule\s*</[^>]+>\s*",
        r"\s*<p[^>]*>\s*Pilots are a company pool\.[\s\S]*?qualified pilots\.\s*</p>\s*",
        r"\s*<[^>]*>\s*Development open aircraft market\s*</[^>]+>\s*",
        r"\s*<p[^>]*>\s*All aircraft models are visible for testing\.[\s\S]*?company budget\.\s*</p>\s*",
        r"\s*<p[^>]*>\s*Pilot qualifications, base level, reputation, endgame locks and\s*progression rules are disabled in this development market\.\s*</p>\s*",
        r"\s*<p[^>]*>\s*Pilot qualifications, base level, reputation, endgame locks and[\s\S]*?development market\.\s*</p>\s*",
        r"\s*<div[^>]*class=[\"'][^\"']*market-note[^\"']*[\"'][^>]*>\s*</div>\s*",
        r"\s*<section[^>]*class=[\"'][^\"']*pilot[^\"']*[\"'][^>]*>\s*</section>\s*",
    ]

    for pattern in patterns:
        text = re.sub(pattern, "\n", text, flags=re.I)

    literal_fragments = [
        "Pilot coverage rule",
        "Pilots are a company pool. They are not assigned permanently to one aircraft,",
        "but each operational aircraft requires coverage by two active qualified pilots.",
        "Development open aircraft market",
        "All aircraft models are visible for testing. Purchase is limited only by company budget.",
        "Pilot qualifications, base level, reputation, endgame locks and",
        "progression rules are disabled in this development market.",
    ]

    for fragment in literal_fragments:
        text = text.replace(fragment, "")

    return text

def add_script_to_html(path: Path, script: str) -> None:
    text = path.read_text(encoding="utf-8")

    if script in text:
        print(f"OK: {path} already includes market filter script")
        return

    if "</body>" in text:
        text = text.replace("</body>", f"  {script}\n</body>")
    else:
        text += "\n" + script + "\n"

    path.write_text(text, encoding="utf-8")
    print(f"OK: added market filter script to {path}")

for path in [
    Path("fleet.html"),
    Path("src/js/fleet.js"),
    Path("src/js/fleet-market-table-dialog.js"),
]:
    if not path.exists():
        print(f"SKIP: {path} not found")
        continue

    original = path.read_text(encoding="utf-8")
    cleaned = remove_market_explanations(original)

    if cleaned != original:
        path.write_text(cleaned, encoding="utf-8")
        print(f"OK: removed market explanatory text from {path}")
    else:
        print(f"OK: no removable market text found in {path}")

if Path("fleet.html").exists():
    add_script_to_html(Path("fleet.html"), '<script src="src/js/aircraft-market-filters.js"></script>')

# Ensure filter script is loaded even if the button/dialog is used on another page.
for page in [Path("index.html"), Path("routes.html")]:
    if page.exists() and "aircraftMarketTableDialog" in page.read_text(encoding="utf-8"):
        add_script_to_html(page, '<script src="src/js/aircraft-market-filters.js"></script>')
