#!/usr/bin/env python3
from pathlib import Path

path = Path("src/js/flight-layer.js")
if not path.exists():
    raise SystemExit("src/js/flight-layer.js not found")

text = path.read_text(encoding="utf-8")

text = text.replace(
    "restoreSelectedFlightRedDashedLine(flight, marker);",
    "showSelectedFlightPath(flight);"
)
text = text.replace(
    "highlightSelectedFlightRoute(flight);",
    "showSelectedFlightPath(flight);"
)

needle = (
    "        window.dispatchEvent(new CustomEvent(\"icaro:aircraft-selected\", {\n"
    "          detail: {\n"
    "            flightInstanceId,\n"
    "            aircraftId,\n"
    "            registrationCode: flight.registration_code || flight.registrationCode || null\n"
    "          }\n"
    "        }));"
)

replacement = (
    "        const selectedAircraftDetail = {\n"
    "          flightInstanceId,\n"
    "          aircraftId,\n"
    "          registrationCode: flight.registration_code || flight.registrationCode || null\n"
    "        };\n\n"
    "        if (typeof window.icaroShowAircraftLivePanel === \"function\") {\n"
    "          window.icaroShowAircraftLivePanel(selectedAircraftDetail);\n"
    "        }\n\n"
    "        window.dispatchEvent(new CustomEvent(\"icaro:aircraft-selected\", {\n"
    "          detail: selectedAircraftDetail\n"
    "        }));"
)

if needle in text and "selectedAircraftDetail" not in text:
    text = text.replace(needle, replacement, 1)
elif "window.dispatchEvent(new CustomEvent(\"icaro:aircraft-selected\"" not in text:
    raise SystemExit("Could not find aircraft-selected dispatch block in src/js/flight-layer.js")

path.write_text(text, encoding="utf-8")
print("OK: aircraft click now uses original showSelectedFlightPath and calls left panel directly.")
