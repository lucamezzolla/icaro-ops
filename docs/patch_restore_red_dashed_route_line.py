#!/usr/bin/env python3
from pathlib import Path

path = Path("src/js/flight-layer.js")

if not path.exists():
    raise SystemExit("src/js/flight-layer.js not found")

text = path.read_text(encoding="utf-8")

# Ensure selected route layer variable exists.
if "let icaroSelectedFlightRouteLayer" not in text:
    insert_at = 0
    for token in ["let icaroFlightLayer", "let flightLayer", "const icaroFlightLayer", "const flightLayer"]:
        pos = text.find(token)
        if pos >= 0:
            insert_at = text.find("\\n", pos) + 1
            break
    text = text[:insert_at] + "let icaroSelectedFlightRouteLayer = null;\\n" + text[insert_at:]

# Add robust helper for selected red dashed route line.
if "function restoreSelectedFlightRedDashedLine(" not in text:
    helper = r'''

function restoreSelectedFlightRedDashedLine(flight, marker = null) {
  const map = window.icaroMap || window.map || window.dashboardMap || window.flightMap;

  if (!window.L || !map) {
    console.warn("Cannot draw selected flight route: Leaflet map not found.");
    return;
  }

  if (icaroSelectedFlightRouteLayer) {
    try {
      map.removeLayer(icaroSelectedFlightRouteLayer);
    } catch (error) {
      console.warn("Unable to remove previous selected route line", error);
    }

    icaroSelectedFlightRouteLayer = null;
  }

  const origin = firstLatLngFlight([
    [flight.origin_latitude, flight.origin_longitude],
    [flight.origin_lat, flight.origin_lng],
    [flight.origin_airport_latitude, flight.origin_airport_longitude],
    [flight.departure_latitude, flight.departure_longitude],
    [flight.departure_airport_latitude, flight.departure_airport_longitude],
    [flight.from_latitude, flight.from_longitude],
    [flight.from_lat, flight.from_lng]
  ]);

  const destination = firstLatLngFlight([
    [flight.destination_latitude, flight.destination_longitude],
    [flight.destination_lat, flight.destination_lng],
    [flight.destination_airport_latitude, flight.destination_airport_longitude],
    [flight.arrival_latitude, flight.arrival_longitude],
    [flight.arrival_airport_latitude, flight.arrival_airport_longitude],
    [flight.to_latitude, flight.to_longitude],
    [flight.to_lat, flight.to_lng]
  ]);

  /*
   * Fallback: if the API object does not expose explicit origin/destination
   * coordinates, try common route geometry fields used by flight layers.
   */
  const routePoints = firstRoutePointsFlight(flight);

  let points = [];

  if (origin && destination) {
    points = [origin, destination];
  } else if (routePoints.length >= 2) {
    points = routePoints;
  } else {
    console.warn("Cannot draw selected flight route: no origin/destination coordinates found on flight object.", flight);
    return;
  }

  icaroSelectedFlightRouteLayer = L.polyline(points, {
    color: "#e53935",
    weight: 3,
    opacity: 0.95,
    dashArray: "8 8",
    interactive: false,
    pane: "overlayPane"
  });

  icaroSelectedFlightRouteLayer.addTo(map);

  try {
    icaroSelectedFlightRouteLayer.bringToFront();
  } catch (error) {
    // Some Leaflet panes/layers may not support bringToFront.
  }
}

function firstLatLngFlight(pairs) {
  for (const pair of pairs) {
    const lat = Number(pair[0]);
    const lng = Number(pair[1]);

    if (Number.isFinite(lat) && Number.isFinite(lng)) {
      return [lat, lng];
    }
  }

  return null;
}

function firstRoutePointsFlight(flight) {
  const candidates = [
    flight.route_points,
    flight.routePoints,
    flight.polyline_points,
    flight.polylinePoints,
    flight.path,
    flight.coordinates
  ];

  for (const candidate of candidates) {
    const normalized = normalizeRoutePointsFlight(candidate);

    if (normalized.length >= 2) {
      return normalized;
    }
  }

  return [];
}

function normalizeRoutePointsFlight(value) {
  if (!value) {
    return [];
  }

  let raw = value;

  if (typeof raw === "string") {
    try {
      raw = JSON.parse(raw);
    } catch (error) {
      return [];
    }
  }

  if (!Array.isArray(raw)) {
    return [];
  }

  const points = [];

  for (const item of raw) {
    if (Array.isArray(item) && item.length >= 2) {
      const lat = Number(item[0]);
      const lng = Number(item[1]);

      if (Number.isFinite(lat) && Number.isFinite(lng)) {
        points.push([lat, lng]);
      }

      continue;
    }

    if (item && typeof item === "object") {
      const lat = Number(firstDefinedFlight(item.lat, item.latitude));
      const lng = Number(firstDefinedFlight(item.lng, item.lon, item.longitude));

      if (Number.isFinite(lat) && Number.isFinite(lng)) {
        points.push([lat, lng]);
      }
    }
  }

  return points;
}

'''
    text += helper

# Replace old highlight call if present with robust helper.
text = text.replace("highlightSelectedFlightRoute(flight);", "restoreSelectedFlightRedDashedLine(flight, marker);")

# Ensure robust helper is called immediately before aircraft-selected event.
if "restoreSelectedFlightRedDashedLine(flight, marker);" not in text:
    needle = 'window.dispatchEvent(new CustomEvent("icaro:aircraft-selected", {'
    if needle not in text:
        raise SystemExit("Could not find aircraft-selected event dispatch in src/js/flight-layer.js")
    text = text.replace(
        needle,
        'restoreSelectedFlightRedDashedLine(flight, marker);\\n\\n        ' + needle,
        1
    )

path.write_text(text, encoding="utf-8")
print("OK: restored robust red dashed route line on aircraft click.")
