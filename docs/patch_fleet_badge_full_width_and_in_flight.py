from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
fleet_html = ROOT / "fleet.html"
fleet_js = ROOT / "src/js/fleet.js"
fleet_css = ROOT / "src/css/fleet.css"

for path in (fleet_html, fleet_js, fleet_css):
    if not path.exists():
        raise SystemExit(f"{path.relative_to(ROOT)} not found")

# 1) fleet.html: make sure the separate airport/last-position column is physically gone.
html = fleet_html.read_text(encoding="utf-8")
original_html = html

html = re.sub(r'\n\s*<th>(?:Airport|Airports|Last position)</th>', '', html, count=1)
html = html.replace('<tr><td colspan="8">Loading...</td></tr>', '<tr><td colspan="7">Loading...</td></tr>')
html = html.replace('<tr><td colspan="8">No owned aircraft yet.</td></tr>', '<tr><td colspan="7">No owned aircraft yet.</td></tr>')

# Remove the old explanatory copy if still present, keeping the Refresh button.
html = re.sub(
    r'<div class="card-header">\s*<div>\s*<h2>Owned aircraft</h2>\s*<p>Essential data only\. Open details for technical and financial information\.</p>\s*</div>\s*(<button id="refreshButton" type="button">Refresh</button>)\s*</div>',
    r'<div class="card-header">\n            \1\n          </div>',
    html,
    count=1,
    flags=re.DOTALL,
)

if html != original_html:
    fleet_html.write_text(html, encoding="utf-8")
    print("Patched fleet.html")
else:
    print("fleet.html already ok")

# 2) fleet.js: status owns the location text; in-flight is displayed as exactly "IN FLIGHT".
js = fleet_js.read_text(encoding="utf-8")
original_js = js

js = js.replace('<tr><td colspan="8">No owned aircraft yet.</td></tr>', '<tr><td colspan="7">No owned aircraft yet.</td></tr>')
js = js.replace('<tr><td colspan="8">Loading...</td></tr>', '<tr><td colspan="7">Loading...</td></tr>')

# Convert table row cells if the old separate airport cell is still present.
patterns = [
    re.compile(
        r'<td><span class="badge \$\{statusClass\(a\.status\)\}">\$\{escapeHtml\(a\.status\)\}</span></td>\s*\n\s*<td>\$\{escapeHtml\(displayAircraftAirport\(a\)\)\}</td>'
    ),
    re.compile(
        r'<td><span class="badge \$\{statusClass\(a\.status\)\}">\$\{escapeHtml\(displayAircraftStatusWithLocation\(a\)\)\}</span></td>\s*\n\s*<td>\$\{escapeHtml\(displayAircraftAirport\(a\)\)\}</td>'
    ),
]
for pattern in patterns:
    js, n = pattern.subn(
        '<td><span class="badge ${statusClass(a.status)}">${escapeHtml(displayAircraftStatusWithLocation(a))}</span></td>',
        js,
        count=1,
    )
    if n:
        break

# If the table already has no airport cell, still ensure it calls the new formatter.
js = js.replace(
    '<td><span class="badge ${statusClass(a.status)}">${escapeHtml(a.status)}</span></td>',
    '<td><span class="badge ${statusClass(a.status)}">${escapeHtml(displayAircraftStatusWithLocation(a))}</span></td>',
    1,
)

new_status_helper = r'''function displayAircraftStatusWithLocation(a) {
  const rawStatus = String(a.status || a.aircraft_status || "-").toUpperCase();
  const status = rawStatus.replace(/_/g, " ");

  if (rawStatus === "IN_FLIGHT") {
    return "IN FLIGHT";
  }

  const location = aircraftLocationLabel(a);
  if (!location || location === "-") {
    return status;
  }

  return `${status} (${location})`;
}

function aircraftLocationLabel(a) {
  const status = String(a.status || a.aircraft_status || "").toUpperCase();

  if (status === "IN_FLIGHT") {
    return "";
  }

  return a.current_airport_icao_code ||
    a.current_airport ||
    a.current_airport_code ||
    a.home_base_icao_code ||
    "-";
}

'''

# Replace an existing helper, or insert it before displayAircraftAirport/statusClass.
if "function displayAircraftStatusWithLocation" in js:
    js = re.sub(
        r'function displayAircraftStatusWithLocation\(a\) \{.*?\n\}\s*\n\s*function aircraftLocationLabel\(a\) \{.*?\n\}\s*\n',
        new_status_helper,
        js,
        count=1,
        flags=re.DOTALL,
    )
else:
    marker = "function displayAircraftAirport(a) {"
    if marker in js:
        js = js.replace(marker, new_status_helper + marker, 1)
    else:
        marker = "function statusClass(status) {"
        if marker not in js:
            raise SystemExit("Could not find insertion point for status/location helpers")
        js = js.replace(marker, new_status_helper + marker, 1)

# Keep old helper safe for other code paths, but do not let it print an airport while in flight.
if "function displayAircraftAirport" in js:
    js = re.sub(
        r'function displayAircraftAirport\(a\) \{.*?\n\}',
        'function displayAircraftAirport(a) {\n  return aircraftLocationLabel(a) || "In flight";\n}',
        js,
        count=1,
        flags=re.DOTALL,
    )

if js != original_js:
    fleet_js.write_text(js, encoding="utf-8")
    print("Patched src/js/fleet.js")
else:
    print("src/js/fleet.js already ok")

# 3) fleet.css: badges inside the owned aircraft table use the full status column width.
css = fleet_css.read_text(encoding="utf-8")
original_css = css
rule = '''

/* Fleet table status badges should fill the whole status column. */
#fleetTableBody .badge {
  display: grid;
  width: 100%;
  box-sizing: border-box;
  text-align: center;
  white-space: nowrap;
}
'''
if "#fleetTableBody .badge" not in css:
    css = css.rstrip() + rule + "\n"

if css != original_css:
    fleet_css.write_text(css, encoding="utf-8")
    print("Patched src/css/fleet.css")
else:
    print("src/css/fleet.css already ok")
