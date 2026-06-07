#!/usr/bin/env python3
from pathlib import Path
import re

path = Path("src/js/flight-layer.js")

if not path.exists():
    raise SystemExit("src/js/flight-layer.js not found")

text = path.read_text(encoding="utf-8")

# 1) Disable aircraft popup binding.
text = re.sub(
    r"\n\s*marker\.bindPopup\(`.*?`\);\n",
    "\n      // Aircraft marker popup disabled: live data is shown in the left Company panel.\n",
    text,
    count=0,
    flags=re.S
)

# 2) Replace / normalize marker click handler.
click_pattern = re.compile(
    r"\n\s*marker\.on\(\"click\",\s*\(\)\s*=>\s*\{.*?\n\s*\}\);\n",
    re.S
)

new_click = '''
      marker.on("click", event => {
        if (event?.originalEvent) {
          L.DomEvent.stopPropagation(event.originalEvent);
          L.DomEvent.preventDefault(event.originalEvent);
        }

        const aircraftId = firstDefinedFlight(
          flight.aircraft_id,
          flight.company_aircraft_id,
          flight.aircraftId
        );

        const flightInstanceId = firstDefinedFlight(
          flight.flight_instance_id,
          flight.flightInstanceId,
          flight.instance_id,
          flight.id
        );

        window.dispatchEvent(new CustomEvent("icaro:aircraft-selected", {
          detail: {
            flightInstanceId,
            aircraftId,
            registrationCode: flight.registration_code || flight.registrationCode || null
          }
        }));
      });
'''

text2, count = click_pattern.subn(new_click, text)

if count == 0:
    marker_add = "marker.addTo(icaroFlightLayer);"
    if marker_add not in text:
        raise SystemExit("Could not find marker click block or marker.addTo(icaroFlightLayer). Send me src/js/flight-layer.js")
    text2 = text.replace(marker_add, new_click + "\n      " + marker_add, 1)

text = text2

# 3) Add DOM ids/classes to Leaflet marker element immediately after addTo.
if "map-aircraft-live-target" not in text:
    text = text.replace(
        "marker.addTo(icaroFlightLayer);",
        '''marker.addTo(icaroFlightLayer);

      const markerElement = marker.getElement?.();
      if (markerElement) {
        markerElement.classList.add("map-aircraft-live-target");
        markerElement.dataset.aircraftId = firstDefinedFlight(
          flight.aircraft_id,
          flight.company_aircraft_id,
          flight.aircraftId
        ) || "";
        markerElement.dataset.flightInstanceId = firstDefinedFlight(
          flight.flight_instance_id,
          flight.flightInstanceId,
          flight.instance_id,
          flight.id
        ) || "";
        markerElement.title = "Click to show aircraft live status";
      }''',
        1
    )

# 4) Add helper for robust field-name handling.
if "function firstDefinedFlight(" not in text:
    text += '''

function firstDefinedFlight(...values) {
  for (const value of values) {
    if (value !== undefined && value !== null && value !== "") {
      return value;
    }
  }

  return null;
}
'''

path.write_text(text, encoding="utf-8")

print("OK: flight-layer.js now sends aircraft clicks to the left panel and disables aircraft popups.")
