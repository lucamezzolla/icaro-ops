#!/usr/bin/env python3
from pathlib import Path

PROJECT = Path.cwd()
ROUTES_JS = PROJECT / "src/js/routes.js"

def read(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path}")
    return path.read_text(encoding="utf-8")

def write(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")

def main() -> None:
    js = read(ROUTES_JS)

    old_filters_html = '''    <div class="button-row">
      <button type="button" id="applyFlightFiltersButton">Apply filters</button>
      <button type="button" id="clearFlightFiltersButton" class="secondary">Clear</button>
    </div>'''

    new_filters_html = '''    <label class="filter-action-cell">
      <span>&nbsp;</span>
      <button type="button" id="clearFlightFiltersButton" class="secondary" title="Clear flight filters">🧹 Clear</button>
    </label>'''

    if old_filters_html in js:
        js = js.replace(old_filters_html, new_filters_html, 1)

    old_apply_listener = '''  filters.querySelector("#applyFlightFiltersButton")?.addEventListener("click", () => {
    flightFiltersApplied = true;
    renderFlights(getVisibleFlightsForCurrentFilters());
  });

'''

    if old_apply_listener in js:
        js = js.replace(old_apply_listener, "", 1)

    old_clear_listener = '''  filters.querySelector("#clearFlightFiltersButton")?.addEventListener("click", () => {
    flightFiltersApplied = false;
    filters.querySelector("#flightDepartureFilter").value = "";
    filters.querySelector("#flightArrivalFilter").value = "";
    filters.querySelector("#flightAirplaneFilter").value = "";
    filters.querySelector("#flightScheduledFilter").value = "";
    renderFlights([]);
  });'''

    new_live_listeners = '''  ["#flightDepartureFilter", "#flightArrivalFilter", "#flightAirplaneFilter"].forEach(selector => {
    filters.querySelector(selector)?.addEventListener("input", applyFlightFiltersLive);
  });

  filters.querySelector("#flightScheduledFilter")?.addEventListener("change", applyFlightFiltersLive);

  filters.querySelector("#clearFlightFiltersButton")?.addEventListener("click", () => {
    flightFiltersApplied = false;
    filters.querySelector("#flightDepartureFilter").value = "";
    filters.querySelector("#flightArrivalFilter").value = "";
    filters.querySelector("#flightAirplaneFilter").value = "";
    filters.querySelector("#flightScheduledFilter").value = "";
    renderFlights([]);
  });'''

    if old_clear_listener in js:
        js = js.replace(old_clear_listener, new_live_listeners, 1)
    elif "applyFlightFiltersLive" not in js:
        raise RuntimeError("Could not find the filters listener block in src/js/routes.js")

    if "function applyFlightFiltersLive(" not in js:
        marker = "\nfunction getVisibleFlightsForCurrentFilters() {"
        helper = '''
function applyFlightFiltersLive() {
  flightFiltersApplied = hasActiveFlightFilters();
  renderFlights(getVisibleFlightsForCurrentFilters());
}

function hasActiveFlightFilters() {
  return Boolean(
    normalizedFilterValue("#flightDepartureFilter") ||
    normalizedFilterValue("#flightArrivalFilter") ||
    normalizedFilterValue("#flightAirplaneFilter") ||
    String(document.querySelector("#flightScheduledFilter")?.value || "").trim()
  );
}
'''
        if marker not in js:
            raise RuntimeError("Could not find getVisibleFlightsForCurrentFilters() in src/js/routes.js")
        js = js.replace(marker, helper + marker, 1)

    old_visible_start = '''function getVisibleFlightsForCurrentFilters() {
  if (!flightFiltersApplied) {
    return [];
  }'''

    new_visible_start = '''function getVisibleFlightsForCurrentFilters() {
  if (!flightFiltersApplied || !hasActiveFlightFilters()) {
    return [];
  }'''

    if old_visible_start in js:
        js = js.replace(old_visible_start, new_visible_start, 1)

    write(ROUTES_JS, js)
    print("Patched Flights filters: live filtering enabled and Clear moved inline with an icon.")

if __name__ == "__main__":
    main()
