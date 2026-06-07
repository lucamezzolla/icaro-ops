#!/usr/bin/env python3
from pathlib import Path
import re

path = Path("src/js/fleet.js")
if not path.exists():
    raise SystemExit("src/js/fleet.js not found")

text = path.read_text(encoding="utf-8")

replacements = [
    ("${escapeHtml(a.current_airport_icao_code || \"-\")}", "${escapeHtml(displayAircraftAirport(a))}"),
    ("${escapeHtml(a.current_airport || \"-\")}", "${escapeHtml(displayAircraftAirport(a))}"),
    ("${escapeHtml(a.current_airport_icao_code ?? \"-\")}", "${escapeHtml(displayAircraftAirport(a))}"),
]

changed = False
for old, new in replacements:
    if old in text:
        text = text.replace(old, new)
        changed = True

if not changed:
    text2 = re.sub(
        r"<td>\s*\$\{escapeHtml\(a\.current_airport_icao_code\s*(?:\|\||\?\?)\s*[\"']-[\"']\)\}\s*</td>",
        "<td>${escapeHtml(displayAircraftAirport(a))}</td>",
        text,
        count=1,
        flags=re.S,
    )
    changed = text2 != text
    text = text2

if not changed:
    print("WARN: could not find current airport rendering expression. Check Fleet table manually.")
else:
    print("OK: Fleet airport column now hides airport for IN_FLIGHT aircraft.")

helper = """
function displayAircraftAirport(a) {
  const status = String(a.status || a.aircraft_status || "").toUpperCase();

  if (status === "IN_FLIGHT") {
    return "-";
  }

  return a.current_airport_icao_code ||
    a.current_airport ||
    a.current_airport_code ||
    a.home_base_icao_code ||
    "-";
}

"""

if "function displayAircraftAirport(" not in text:
    marker = "function escapeHtml"
    if marker in text:
        text = text.replace(marker, helper + marker, 1)
    else:
        text += "\n" + helper

path.write_text(text, encoding="utf-8")
