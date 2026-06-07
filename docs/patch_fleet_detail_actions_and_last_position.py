from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
fleet_html = ROOT / "fleet.html"
fleet_js = ROOT / "src/js/fleet.js"

if not fleet_html.exists():
    raise SystemExit("fleet.html not found")
if not fleet_js.exists():
    raise SystemExit("src/js/fleet.js not found")

html = fleet_html.read_text(encoding="utf-8")
html2 = html
html2 = html2.replace("<th>Airport</th>", "<th>Last position</th>")
html2 = html2.replace("<th>Airports</th>", "<th>Last position</th>")
if html2 != html:
    fleet_html.write_text(html2, encoding="utf-8")
    print("Patched fleet.html")
else:
    print("fleet.html already patched or header not found")

js = fleet_js.read_text(encoding="utf-8")
original = js

# Remove Image and Maintenance actions from the owned aircraft Fleet table, keeping only Details.
js = re.sub(
    r"\n\s*<button type=\"button\" data-aircraft-image=\"\$\{a\.aircraft_id\}\" class=\"secondary\">Image</button>\s*",
    "\n",
    js,
)
js = re.sub(
    r"\n\s*<a class=\"button-link\" href=\"maintenance\.html\?aircraftId=\$\{encodeURIComponent\(a\.aircraft_id\)\}\">Maintenance</a>\s*",
    "\n",
    js,
)

# Remove table-level Image button listener block if present. Image can still be opened from aircraft detail.
js = re.sub(
    r"\n\s*tbody\.querySelectorAll\(\"\[data-aircraft-image\]\"\)\.forEach\(button => \{\s*\n\s*button\.addEventListener\(\"click\", \(\) => openAircraftImage\(Number\(button\.dataset\.aircraftImage\)\)\);\s*\n\s*\}\);\s*",
    "\n",
    js,
    flags=re.MULTILINE,
)

# Ensure the detail view binds its own Image action after rendering.
needle = "content.innerHTML = renderAircraftDetail(a, data.recent_flights || []);"
replacement = "content.innerHTML = renderAircraftDetail(a, data.recent_flights || []);\n    bindAircraftDetailActions(content, a);"
if needle in js and replacement not in js:
    js = js.replace(needle, replacement, 1)

# Add an Actions section near the bottom of aircraft detail, before the closing detail-grid div.
actions_section = '''
      <section class="detail-section aircraft-detail-actions">
        <h3>Actions</h3>
        <div class="button-row">
          <button type="button" data-aircraft-detail-image="${a.aircraft_id}" class="secondary">Image</button>
          <a class="button-link" href="maintenance.html?aircraftId=${encodeURIComponent(a.aircraft_id)}">Maintenance</a>
        </div>
      </section>'''
if "aircraft-detail-actions" not in js:
    insert_after = '''      <section class="detail-section">
        <h3>Pilot coverage</h3>
        <p class="muted">
          This aircraft does not have permanently assigned pilots. It is covered by the company pool of active qualified pilots.
          Dispatch will use available qualified pilots for each flight.
        </p>
      </section>'''
    if insert_after in js:
        js = js.replace(insert_after, insert_after + actions_section, 1)
    else:
        # Fallback: insert before the final detail-grid close in renderAircraftDetail.
        js = js.replace("\n    </div>\n  `;\n}\n\nfunction openAircraftImage", actions_section + "\n    </div>\n  `;\n}\n\nfunction openAircraftImage", 1)

# Add helper for detail action binding, before openAircraftImage.
helper = '''
function bindAircraftDetailActions(container, aircraft) {
  container.querySelectorAll("[data-aircraft-detail-image]").forEach(button => {
    button.addEventListener("click", () => openAircraftImage(Number(aircraft.aircraft_id)));
  });
}

'''
if "function bindAircraftDetailActions" not in js:
    marker = "function openAircraftImage(aircraftId) {"
    if marker not in js:
        raise SystemExit("Could not find openAircraftImage insertion point")
    js = js.replace(marker, helper + marker, 1)

# When an aircraft is currently flying, Last position should say In flight instead of an airport code or dash.
js = re.sub(
    r'if \(status === "IN_FLIGHT"\) \{\s*return "[^"]*";\s*\}',
    'if (status === "IN_FLIGHT") {\n    return "In flight";\n  }',
    js,
    count=1,
    flags=re.MULTILINE,
)

if js != original:
    fleet_js.write_text(js, encoding="utf-8")
    print("Patched src/js/fleet.js")
else:
    print("src/js/fleet.js already patched or expected snippets not found")
