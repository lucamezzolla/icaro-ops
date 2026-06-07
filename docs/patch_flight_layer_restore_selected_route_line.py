#!/usr/bin/env python3
from pathlib import Path

path = Path("src/js/flight-layer.js")

if not path.exists():
    raise SystemExit("src/js/flight-layer.js not found")

text = path.read_text(encoding="utf-8")

# Add/ensure a selected route layer variable.
if "let icaroSelectedFlightRouteLayer" not in text:
    insert_after = None
    for candidate in [
        "let icaroFlightLayer",
        "let flightLayer",
        "const FLIGHT"
    ]:
        pos = text.find(candidate)
        if pos != -1:
            line_end = text.find("\n", pos)
            insert_after = line_end + 1
            break

    if insert_after is None:
        insert_after = 0

    text = text[:insert_after] + "let icaroSelectedFlightRouteLayer = null;\n" + text[insert_after:]

# Add helper that redraws the red dashed line for the selected aircraft route.
if "function highlightSelectedFlightRoute(" not in text:
    helper = '''

function highlightSelectedFlightRoute(flight) {
  if (!window.L || !window.icaroMap) {
    return;
  }

  if (icaroSelectedFlightRouteLayer) {
    try {
      icaroMap.removeLayer(icaroSelectedFlightRouteLayer);
    } catch (error) {
      console.warn("Unable to remove previous selected flight route", error);
    }

    icaroSelectedFlightRouteLayer = null;
  }

  const originLat = Number(firstDefinedFlight(
    flight.origin_latitude,
    flight.origin_lat,
    flight.origin_airport_latitude,
    flight.departure_latitude
  ));

  const originLng = Number(firstDefinedFlight(
    flight.origin_longitude,
    flight.origin_lng,
    flight.origin_airport_longitude,
    flight.departure_longitude
  ));

  const destinationLat = Number(firstDefinedFlight(
    flight.destination_latitude,
    flight.destination_lat,
    flight.destination_airport_latitude,
    flight.arrival_latitude
  ));

  const destinationLng = Number(firstDefinedFlight(
    flight.destination_longitude,
    flight.destination_lng,
    flight.destination_airport_longitude,
    flight.arrival_longitude
  ));

  if (
    !Number.isFinite(originLat) ||
    !Number.isFinite(originLng) ||
    !Number.isFinite(destinationLat) ||
    !Number.isFinite(destinationLng)
  ) {
    return;
  }

  icaroSelectedFlightRouteLayer = L.polyline(
    [
      [originLat, originLng],
      [destinationLat, destinationLng]
    ],
    {
      color: "#e53935",
      weight: 3,
      opacity: 0.95,
      dashArray: "8 8",
      interactive: false
    }
  );

  icaroSelectedFlightRouteLayer.addTo(icaroMap);
}

'''
    text += helper

# Call helper inside the aircraft marker click handler before dispatching the event.
if "highlightSelectedFlightRoute(flight);" not in text:
    needle = 'window.dispatchEvent(new CustomEvent("icaro:aircraft-selected", {'
    if needle not in text:
        raise SystemExit("Could not find aircraft-selected event dispatch in src/js/flight-layer.js")
    text = text.replace(
        needle,
        'highlightSelectedFlightRoute(flight);\n\n        ' + needle,
        1
    )

path.write_text(text, encoding="utf-8")
print("OK: aircraft click now restores the red dashed selected route line.")
