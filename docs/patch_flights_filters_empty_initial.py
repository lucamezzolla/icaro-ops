#!/usr/bin/env python3
from pathlib import Path
import re

PROJECT = Path.cwd()
ROUTES_JS = PROJECT / "src/js/routes.js"
ROUTES_HTML = PROJECT / "routes.html"

FILTER_HELPERS = 'function setupFlightFilters() {\n  if (document.querySelector("#flightTableFilters")) {\n    return;\n  }\n\n  const table = document.querySelector("#routesTableBody")?.closest("table");\n  if (!table) {\n    return;\n  }\n\n  const filters = document.createElement("section");\n  filters.id = "flightTableFilters";\n  filters.className = "filter-panel";\n  filters.innerHTML = `\n    <div class="filter-grid">\n      <label>\n        <span>Departure</span>\n        <input type="text" id="flightDepartureFilter" placeholder="ICAO, city, airport">\n      </label>\n      <label>\n        <span>Arrival</span>\n        <input type="text" id="flightArrivalFilter" placeholder="ICAO, city, airport">\n      </label>\n      <label>\n        <span>Airplane</span>\n        <input type="text" id="flightAirplaneFilter" placeholder="ICAO type, model, manufacturer">\n      </label>\n      <label>\n        <span>Scheduled</span>\n        <select id="flightScheduledFilter">\n          <option value="">Any</option>\n          <option value="SCHEDULED">Scheduled</option>\n          <option value="ON_DEMAND">On demand</option>\n        </select>\n      </label>\n    </div>\n    <div class="button-row">\n      <button type="button" id="applyFlightFiltersButton">Apply filters</button>\n      <button type="button" id="clearFlightFiltersButton" class="secondary">Clear</button>\n    </div>\n  `;\n\n  table.parentNode.insertBefore(filters, table);\n\n  filters.querySelector("#applyFlightFiltersButton")?.addEventListener("click", () => {\n    flightFiltersApplied = true;\n    renderFlights(getVisibleFlightsForCurrentFilters());\n  });\n\n  filters.querySelector("#clearFlightFiltersButton")?.addEventListener("click", () => {\n    flightFiltersApplied = false;\n    filters.querySelector("#flightDepartureFilter").value = "";\n    filters.querySelector("#flightArrivalFilter").value = "";\n    filters.querySelector("#flightAirplaneFilter").value = "";\n    filters.querySelector("#flightScheduledFilter").value = "";\n    renderFlights([]);\n  });\n}\n\nfunction getVisibleFlightsForCurrentFilters() {\n  if (!flightFiltersApplied) {\n    return [];\n  }\n\n  const departure = normalizedFilterValue("#flightDepartureFilter");\n  const arrival = normalizedFilterValue("#flightArrivalFilter");\n  const airplane = normalizedFilterValue("#flightAirplaneFilter");\n  const scheduled = String(document.querySelector("#flightScheduledFilter")?.value || "").toUpperCase();\n\n  return flights.filter(flight => {\n    if (departure && !flightDepartureSearchText(flight).includes(departure)) {\n      return false;\n    }\n\n    if (arrival && !flightArrivalSearchText(flight).includes(arrival)) {\n      return false;\n    }\n\n    if (airplane && !flightAirplaneSearchText(flight).includes(airplane)) {\n      return false;\n    }\n\n    if (scheduled && String(flight.service_type || "").toUpperCase() !== scheduled) {\n      return false;\n    }\n\n    return true;\n  });\n}\n\nfunction normalizedFilterValue(selector) {\n  return String(document.querySelector(selector)?.value || "").trim().toUpperCase();\n}\n\nfunction flightDepartureSearchText(flight) {\n  return [\n    flight.origin_airport_icao_code,\n    flight.origin_airport_iata_code,\n    flight.origin_airport_name,\n    flight.origin_city,\n    flight.origin_location_name\n  ].map(value => String(value || "").toUpperCase()).join(" ");\n}\n\nfunction flightArrivalSearchText(flight) {\n  return [\n    flight.destination_airport_icao_code,\n    flight.destination_airport_iata_code,\n    flight.destination_airport_name,\n    flight.destination_city,\n    flight.destination_location_name\n  ].map(value => String(value || "").toUpperCase()).join(" ");\n}\n\nfunction flightAirplaneSearchText(flight) {\n  return [\n    flight.compatible_aircraft_icao_codes,\n    flight.icao_type_code,\n    flight.compatible_aircraft_model_codes,\n    flight.manufacturer,\n    flight.model_name,\n    flight.preferred_aircraft_model_name\n  ].map(value => String(value || "").toUpperCase()).join(" ");\n}\n'

def read(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path}")
    return path.read_text(encoding="utf-8")

def write(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")

def patch_routes_js() -> None:
    js = read(ROUTES_JS)

    if "let flightFiltersApplied = false;" not in js:
        js = js.replace(
            "let flights = [];\n",
            "let flights = [];\nlet flightFiltersApplied = false;\n",
            1
        )

    if "setupFlightFilters();" not in js:
        js = js.replace(
            "  setupDialogCloseButtons();\n",
            "  setupDialogCloseButtons();\n  setupFlightFilters();\n",
            1
        )

    js = js.replace(
        "    renderFlights(flights);\n",
        "    renderFlights(getVisibleFlightsForCurrentFilters());\n",
        1
    )

    if "function setupFlightFilters()" not in js:
        marker = "\nfunction renderFlights(rows) {"
        if marker not in js:
            raise RuntimeError("Could not find renderFlights() marker in src/js/routes.js")
        js = js.replace(marker, "\n" + FILTER_HELPERS.rstrip() + "\n" + marker, 1)

    old_empty = 'tbody.innerHTML = `<tr><td colspan="5">No flights yet.</td></tr>`;'
    new_empty = 'tbody.innerHTML = `<tr><td colspan="5">${flightFiltersApplied ? "No flights match the current filters." : "Use the filters above to show flights."}</td></tr>`;'
    js = js.replace(old_empty, new_empty, 1)

    write(ROUTES_JS, js)

def patch_routes_html() -> None:
    if not ROUTES_HTML.exists():
        return

    html = read(ROUTES_HTML)

    html = html.replace(
        "Create on-demand or scheduled flights and open details for operational rules and generated flight instances.",
        ""
    )

    html = re.sub(
        r'<section\s+class="page-hero">\s*<h1>\s*Flights\s*</h1>\s*<p>\s*</p>\s*</section>',
        '',
        html,
        flags=re.IGNORECASE | re.DOTALL
    )

    html = re.sub(
        r'<header\s+class="page-header">\s*<h1>\s*Flights\s*</h1>\s*<p>\s*</p>\s*</header>',
        '',
        html,
        flags=re.IGNORECASE | re.DOTALL
    )

    html = re.sub(r'\n\s*<p>\s*</p>', '', html)

    write(ROUTES_HTML, html)

def main() -> None:
    patch_routes_js()
    patch_routes_html()
    print("Patched Flights view: removed intro text, added filters, and keeps the table empty until filters are applied.")

if __name__ == "__main__":
    main()
