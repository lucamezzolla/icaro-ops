#!/usr/bin/env python3
from pathlib import Path

PROJECT = Path.cwd()
ROUTES_JS = PROJECT / "src/js/routes.js"
FLEET_JS = PROJECT / "src/js/fleet.js"
ROUTES_CSS = PROJECT / "src/css/routes.css"

NEW_SETUP_FLIGHT_FILTERS = 'function setupFlightFilters() {\n  if (document.querySelector("#flightTableFilters")) {\n    return;\n  }\n\n  const table = document.querySelector("#routesTableBody")?.closest("table");\n  if (!table) {\n    return;\n  }\n\n  const filters = document.createElement("section");\n  filters.id = "flightTableFilters";\n  filters.className = "aircraft-market-filter-panel flight-filter-panel";\n  filters.setAttribute("aria-label", "Flight filters");\n  filters.innerHTML = `\n    <div class="aircraft-market-filters flight-filters">\n      <label>\n        <span>Departure</span>\n        <input type="text" id="flightDepartureFilter" placeholder="ICAO, city, airport">\n      </label>\n\n      <label>\n        <span>Arrival</span>\n        <input type="text" id="flightArrivalFilter" placeholder="ICAO, city, airport">\n      </label>\n\n      <label>\n        <span>Airplane</span>\n        <input type="text" id="flightAirplaneFilter" placeholder="ICAO type code">\n      </label>\n\n      <label>\n        <span>Scheduled</span>\n        <select id="flightScheduledFilter">\n          <option value="">Any</option>\n          <option value="SCHEDULED">Scheduled</option>\n          <option value="ON_DEMAND">On demand</option>\n        </select>\n      </label>\n\n      <button type="button" id="clearFlightFiltersButton" class="secondary" title="Clear flight filters">🧹 Clear</button>\n    </div>\n\n    <p class="muted aircraft-market-filter-summary" id="flightFilterSummary">\n      Showing 0 of 0 flights.\n    </p>\n  `;\n\n  table.parentNode.insertBefore(filters, table);\n\n  ["#flightDepartureFilter", "#flightArrivalFilter", "#flightAirplaneFilter"].forEach(selector => {\n    filters.querySelector(selector)?.addEventListener("input", applyFlightFiltersLive);\n  });\n\n  filters.querySelector("#flightScheduledFilter")?.addEventListener("change", applyFlightFiltersLive);\n\n  filters.querySelector("#clearFlightFiltersButton")?.addEventListener("click", () => {\n    flightFiltersApplied = false;\n    filters.querySelector("#flightDepartureFilter").value = "";\n    filters.querySelector("#flightArrivalFilter").value = "";\n    filters.querySelector("#flightAirplaneFilter").value = "";\n    filters.querySelector("#flightScheduledFilter").value = "";\n    renderFlights([]);\n  });\n\n  updateFlightFilterSummary(0);\n}'
CSS_APPEND = '\n/* Unified filter panel, aligned with the Buy new aircraft market filters. */\n.aircraft-market-filter-panel,\n.flight-filter-panel {\n  margin: 0 0 16px;\n  padding: 14px;\n  border: 1px solid rgba(255,255,255,.12);\n  border-radius: 18px;\n  background: rgba(255,255,255,.05);\n}\n\n.aircraft-market-filters,\n.flight-filters {\n  display: grid;\n  grid-template-columns: repeat(5, minmax(140px, 1fr));\n  gap: 12px;\n  align-items: end;\n}\n\n.aircraft-market-filters label,\n.flight-filters label {\n  display: grid;\n  gap: 6px;\n}\n\n.aircraft-market-filters label span,\n.flight-filters label span {\n  color: var(--muted);\n  font-size: .78rem;\n  font-weight: 800;\n  text-transform: uppercase;\n  letter-spacing: .07em;\n}\n\n.aircraft-market-filters input,\n.aircraft-market-filters select,\n.flight-filters input,\n.flight-filters select {\n  width: 100%;\n  min-height: 38px;\n  border: 1px solid rgba(255,255,255,.16);\n  border-radius: 12px;\n  padding: 8px 10px;\n  color: var(--text);\n  background: rgba(0,0,0,.18);\n}\n\n.aircraft-market-filters input:focus,\n.aircraft-market-filters select:focus,\n.flight-filters input:focus,\n.flight-filters select:focus {\n  outline: 2px solid rgba(115,215,255,.38);\n  border-color: rgba(115,215,255,.70);\n}\n\n.aircraft-market-filters button,\n.flight-filters button {\n  min-height: 38px;\n  align-self: end;\n  white-space: nowrap;\n}\n\n.aircraft-market-filter-summary {\n  margin: 10px 0 0;\n}\n\n@media(max-width:1100px) {\n  .aircraft-market-filters,\n  .flight-filters {\n    grid-template-columns: repeat(2, minmax(0, 1fr));\n  }\n}\n\n@media(max-width:640px) {\n  .aircraft-market-filters,\n  .flight-filters {\n    grid-template-columns: 1fr;\n  }\n}\n'

def read(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path}")
    return path.read_text(encoding="utf-8")

def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")

def replace_function(content: str, function_name: str, new_function: str) -> str:
    marker = "function " + function_name + "("
    start = content.find(marker)
    if start < 0:
        raise RuntimeError(f"Function not found: {function_name}")

    brace = content.find("{", start)
    if brace < 0:
        raise RuntimeError(f"Opening brace not found for: {function_name}")

    depth = 0
    i = brace
    in_string = None
    escape = False
    in_line_comment = False
    in_block_comment = False
    template_depth = 0

    while i < len(content):
        ch = content[i]
        nxt = content[i + 1] if i + 1 < len(content) else ""

        if in_line_comment:
            if ch == "\n":
                in_line_comment = False
            i += 1
            continue

        if in_block_comment:
            if ch == "*" and nxt == "/":
                in_block_comment = False
                i += 2
                continue
            i += 1
            continue

        if in_string:
            if escape:
                escape = False
                i += 1
                continue
            if ch == "\\":
                escape = True
                i += 1
                continue
            if in_string == "`":
                if ch == "$" and nxt == "{":
                    template_depth += 1
                    i += 2
                    continue
                if ch == "}" and template_depth > 0:
                    template_depth -= 1
                    i += 1
                    continue
                if ch == "`" and template_depth == 0:
                    in_string = None
                    i += 1
                    continue
            elif ch == in_string:
                in_string = None
                i += 1
                continue
            i += 1
            continue

        if ch == "/" and nxt == "/":
            in_line_comment = True
            i += 2
            continue
        if ch == "/" and nxt == "*":
            in_block_comment = True
            i += 2
            continue
        if ch in ("'", '"', "`"):
            in_string = ch
            i += 1
            continue

        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return content[:start] + new_function.rstrip() + content[i + 1:]

        i += 1

    raise RuntimeError(f"Could not find end of function: {function_name}")

def patch_routes_js() -> None:
    js = read(ROUTES_JS)

    js = replace_function(js, "setupFlightFilters", NEW_SETUP_FLIGHT_FILTERS)

    if "function updateFlightFilterSummary(" not in js:
        helper = """
function updateFlightFilterSummary(visibleCount = 0) {
  const summary = document.querySelector("#flightFilterSummary");
  if (!summary) {
    return;
  }

  summary.textContent = `Showing ${visibleCount} of ${flights.length} flights.`;
}
"""
        marker = "\nfunction applyFlightFiltersLive() {"
        if marker not in js:
            raise RuntimeError("Could not find applyFlightFiltersLive marker.")
        js = js.replace(marker, "\n" + helper.rstrip() + "\n" + marker, 1)

    if "updateFlightFilterSummary(rows.length);" not in js:
        old_render_start = """function renderFlights(rows) {
  const tbody = document.querySelector("#routesTableBody");"""
        new_render_start = """function renderFlights(rows) {
  updateFlightFilterSummary(rows.length);
  const tbody = document.querySelector("#routesTableBody");"""
        if old_render_start not in js:
            raise RuntimeError("Could not find renderFlights start.")
        js = js.replace(old_render_start, new_render_start, 1)

    js = js.replace('placeholder="ICAO type, model, manufacturer"', 'placeholder="ICAO type code"')

    write(ROUTES_JS, js)

def patch_fleet_js() -> None:
    js = read(FLEET_JS)

    js = js.replace(
        '<button type="button" class="secondary" id="aircraftMarketClearFilters">Clear filters</button>',
        '<button type="button" class="secondary" id="aircraftMarketClearFilters" title="Clear aircraft market filters">🧹 Clear</button>'
    )

    write(FLEET_JS, js)

def patch_routes_css() -> None:
    css = read(ROUTES_CSS)

    if "Unified filter panel, aligned with the Buy new aircraft market filters" not in css:
        css = css.rstrip() + "\n\n" + CSS_APPEND.strip() + "\n"

    write(ROUTES_CSS, css)

def main() -> None:
    patch_routes_js()
    patch_fleet_js()
    patch_routes_css()
    print("Patched unified filter UI for Flights and Buy new aircraft.")

if __name__ == "__main__":
    main()
