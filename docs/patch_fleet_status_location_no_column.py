from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
fleet_html = ROOT / "fleet.html"
fleet_js = ROOT / "src/js/fleet.js"

if not fleet_html.exists():
    raise SystemExit("fleet.html not found")
if not fleet_js.exists():
    raise SystemExit("src/js/fleet.js not found")

# --- fleet.html: remove the physical Last position/Airport column from the owned aircraft table.
html = fleet_html.read_text(encoding="utf-8")
html_original = html

# Remove the old explanatory card title/subtitle if it is still present, keeping Refresh.
html = re.sub(
    r'<div class="card-header">\s*<div>\s*<h2>Owned aircraft</h2>\s*<p>Essential data only\. Open details for technical and financial information\.</p>\s*</div>\s*(<button id="refreshButton" type="button">Refresh</button>)\s*</div>',
    r'<div class="card-header">\n            \1\n          </div>',
    html,
    count=1,
    flags=re.DOTALL,
)

# Remove whichever header name is currently used for the aircraft position column.
html = re.sub(r'\n\s*<th>(?:Airport|Airports|Last position)</th>', '', html, count=1)

# The owned aircraft table loses one column: 8 -> 7.
html = html.replace('<tr><td colspan="8">Loading...</td></tr>', '<tr><td colspan="7">Loading...</td></tr>')
html = html.replace('<tr><td colspan="8">No owned aircraft yet.</td></tr>', '<tr><td colspan="7">No owned aircraft yet.</td></tr>')

if html != html_original:
    fleet_html.write_text(html, encoding="utf-8")
    print("Patched fleet.html")
else:
    print("fleet.html already patched or expected snippets not found")

# --- fleet.js: status now includes current location, and the separate position column is removed.
js = fleet_js.read_text(encoding="utf-8")
js_original = js

js = js.replace('<tr><td colspan="8">No owned aircraft yet.</td></tr>', '<tr><td colspan="7">No owned aircraft yet.</td></tr>')

# Replace the Status cell + following position cell with a single richer Status cell.
status_and_location_pattern = re.compile(
    r'<td><span class="badge \$\{statusClass\(a\.status\)\}">\$\{escapeHtml\((?:a\.status|displayAircraftStatusWithLocation\(a\))\)\}</span></td>\s*\n\s*<td>\$\{escapeHtml\(displayAircraftAirport\(a\)\)\}</td>',
    re.MULTILINE,
)
js, replaced = status_and_location_pattern.subn(
    '<td><span class="badge ${statusClass(a.status)}">${escapeHtml(displayAircraftStatusWithLocation(a))}</span></td>',
    js,
    count=1,
)

# Fallback for slightly different whitespace or already edited status cell.
if replaced == 0:
    status_cell = '<td><span class="badge ${statusClass(a.status)}">${escapeHtml(a.status)}</span></td>'
    location_cell_pattern = re.compile(r'\s*<td>\$\{escapeHtml\(displayAircraftAirport\(a\)\)\}</td>')
    if status_cell in js:
        js = js.replace(status_cell, '<td><span class="badge ${statusClass(a.status)}">${escapeHtml(displayAircraftStatusWithLocation(a))}</span></td>', 1)
        js = location_cell_pattern.sub('', js, count=1)

helper = r'''
function displayAircraftStatusWithLocation(a) {
  const status = String(a.status || a.aircraft_status || "-").toUpperCase();
  const location = aircraftLocationLabel(a);

  if (!location || location === "-") {
    return status;
  }

  return `${status} (${location})`;
}

function aircraftLocationLabel(a) {
  const status = String(a.status || a.aircraft_status || "").toUpperCase();

  if (status === "IN_FLIGHT") {
    return "In flight";
  }

  return a.current_airport_icao_code ||
    a.current_airport ||
    a.current_airport_code ||
    a.home_base_icao_code ||
    "-";
}

'''

if "function displayAircraftStatusWithLocation" not in js:
    marker = "function displayAircraftAirport(a) {"
    if marker in js:
        js = js.replace(marker, helper + marker, 1)
    else:
        marker = "function statusClass(status) {"
        if marker not in js:
            raise SystemExit("Could not find insertion point for status/location helpers")
        js = js.replace(marker, helper + marker, 1)

# Keep legacy helper safe in case other code still calls it.
js = re.sub(
    r'function displayAircraftAirport\(a\) \{.*?\n\}',
    'function displayAircraftAirport(a) {\n  return aircraftLocationLabel(a);\n}',
    js,
    count=1,
    flags=re.DOTALL,
)

if js != js_original:
    fleet_js.write_text(js, encoding="utf-8")
    print("Patched src/js/fleet.js")
else:
    print("src/js/fleet.js already patched or expected snippets not found")
