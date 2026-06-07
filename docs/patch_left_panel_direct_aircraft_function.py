#!/usr/bin/env python3
from pathlib import Path

path = Path("src/js/map-aircraft-left-panel.js")
if not path.exists():
    raise SystemExit("src/js/map-aircraft-left-panel.js not found")

text = path.read_text(encoding="utf-8")

exposure = """
    window.icaroShowAircraftLivePanel = async detail => {
      const safeDetail = detail || {};
      const flightInstanceId = safeDetail.flightInstanceId || safeDetail.flight_instance_id;

      if (flightInstanceId) {
        await showFlightInLeftPanel(flightInstanceId);
        return;
      }

      const aircraftId = safeDetail.aircraftId || safeDetail.aircraft_id;

      if (aircraftId && activeFlightByAircraftId.has(String(aircraftId))) {
        const flight = activeFlightByAircraftId.get(String(aircraftId));
        await showFlightInLeftPanel(flight.flight_instance_id);
      }
    };

    window.addEventListener("icaro:aircraft-selected", async event => {
      if (typeof window.icaroShowAircraftLivePanel === "function") {
        await window.icaroShowAircraftLivePanel(event.detail || {});
      }
    });
"""

if "window.icaroShowAircraftLivePanel" not in text:
    marker = "    bindMapClicks();"
    if marker not in text:
        raise SystemExit("Could not find bindMapClicks() in src/js/map-aircraft-left-panel.js")
    text = text.replace(marker, marker + "\n" + exposure, 1)

path.write_text(text, encoding="utf-8")
print("OK: left panel exposes window.icaroShowAircraftLivePanel and listens to aircraft events.")
