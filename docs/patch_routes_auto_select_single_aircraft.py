#!/usr/bin/env python3
from pathlib import Path

path = Path("src/js/routes.js")
text = path.read_text(encoding="utf-8")

old = '''    const aircraftId = await chooseAircraftForOnDemandFlight(data.flight, available);

    if (!aircraftId) {
      return;
    }'''

new = '''    let aircraftId = null;

    if (available.length === 1) {
      aircraftId = Number(available[0].company_aircraft_id || available[0].aircraft_id);
    } else {
      aircraftId = await chooseAircraftForOnDemandFlight(data.flight, available);
    }

    if (!aircraftId) {
      return;
    }'''

if old not in text:
    raise SystemExit("Could not find aircraft-choice block in src/js/routes.js. Send me the current startFlightNow function.")

text = text.replace(old, new)

path.write_text(text, encoding="utf-8")
print("OK: routes.js auto-selects the only available aircraft and asks only when multiple are available.")
