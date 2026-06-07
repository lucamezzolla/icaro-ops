#!/usr/bin/env python3
from pathlib import Path

path = Path("src/js/map-aircraft-left-panel.js")

if not path.exists():
    raise SystemExit("src/js/map-aircraft-left-panel.js not found")

text = path.read_text(encoding="utf-8")

listener = '''
  window.addEventListener("icaro:aircraft-selected", async event => {
    const detail = event.detail || {};
    const flightInstanceId = detail.flightInstanceId;

    if (flightInstanceId) {
      await showFlightInLeftPanel(flightInstanceId);
      return;
    }

    const aircraftId = detail.aircraftId;

    if (aircraftId && activeFlightByAircraftId.has(String(aircraftId))) {
      const flight = activeFlightByAircraftId.get(String(aircraftId));
      await showFlightInLeftPanel(flight.flight_instance_id);
    }
  });
'''

if 'icaro:aircraft-selected' not in text:
    marker = "    bindMapClicks();"
    if marker not in text:
        raise SystemExit("Could not find bindMapClicks() in src/js/map-aircraft-left-panel.js")
    text = text.replace(marker, marker + "\n" + listener, 1)

old_base = '''  const BASE_SELECTORS = [
    "[data-base-id]",
    "[data-airport-base]",
    "[data-company-base]",
    ".base-marker",
    ".airport-base-marker",
    ".rival-base-marker"
  ];'''

new_base = '''  const BASE_SELECTORS = [
    "[data-base-id]",
    "[data-airport-base]",
    "[data-company-base]",
    ".base-marker",
    ".hq-marker",
    ".airport-base-marker",
    ".rival-base-marker",
    ".other-player-base-marker"
  ];'''

if old_base in text:
    text = text.replace(old_base, new_base)

old_panel = '''  const COMPANY_PANEL_SELECTORS = [
    "#companyPanel",
    "#companyInfoPanel",
    "#companyOverview",
    "#leftPanel",
    "#sidebar",
    ".company-panel",
    ".company-overview",
    ".left-panel",
    ".sidebar"
  ];'''

new_panel = '''  const COMPANY_PANEL_SELECTORS = [
    "#mapSidebar",
    "#dashboardSidebar",
    "#baseSidebar",
    "#companyPanel",
    "#companyInfoPanel",
    "#companyOverview",
    "#leftPanel",
    "#sidebar",
    ".map-sidebar",
    ".dashboard-sidebar",
    ".base-sidebar",
    ".company-panel",
    ".company-overview",
    ".left-panel",
    ".sidebar"
  ];'''

if old_panel in text:
    text = text.replace(old_panel, new_panel)

path.write_text(text, encoding="utf-8")

print("OK: map-aircraft-left-panel.js now listens to direct aircraft marker click events.")
