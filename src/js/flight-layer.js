/*
 * Optional map flight layer.
 *
 * To enable this on index.html, include this script after dashboard-map.js,
 * and expose the Leaflet map in dashboard-map.js with:
 *
 *   window.icaroOpsMap = map;
 *
 * after the map is created in initMap().
 */

const ICARO_FLIGHT_API = {
  activeFlights: "api/public/flights/active.php"
};

let icaroFlightLayer = null;
let icaroSelectedFlightRouteLayer = null;
let icaroSelectedFlightPathLayer = null;
const ICARO_FLIGHT_REFRESH_MS = 5000;

document.addEventListener("DOMContentLoaded", () => {
  setTimeout(initIcaroFlightLayer, 500);
});

function initIcaroFlightLayer() {
  if (!window.icaroOpsMap || typeof L === "undefined") {
    return;
  }

  icaroFlightLayer = L.layerGroup().addTo(window.icaroOpsMap);

  refreshIcaroFlights();
  setInterval(refreshIcaroFlights, ICARO_FLIGHT_REFRESH_MS);

  document.addEventListener("visibilitychange", () => {
    if (!document.hidden) {
      refreshIcaroFlights();
    }
  });

  window.addEventListener("focus", refreshIcaroFlights);
}

async function refreshIcaroFlights() {
  if (!window.icaroOpsMap || !icaroFlightLayer) {
    return;
  }

  try {
    const response = await fetch(ICARO_FLIGHT_API.activeFlights, {
      headers: { "Accept": "application/json" },
      credentials: "same-origin"
    });

    if (!response.ok) {
      return;
    }

    const flights = await response.json();

    icaroFlightLayer.clearLayers();

    for (const flight of flights) {
      const position = interpolateFlightPosition(flight);
      if (!position) continue;

      const marker = L.marker([position.lat, position.lng], {
        icon: L.divIcon({
          className: "flight-aircraft-leaflet-icon",
          html: aircraftMarkerSvg(calculateBearingDegrees(
            Number(flight.origin_latitude),
            Number(flight.origin_longitude),
            Number(flight.destination_latitude),
            Number(flight.destination_longitude)
          )),
          iconSize: [34, 34],
          iconAnchor: [17, 17],
          popupAnchor: [0, -16]
        }),
        title: `${flight.flight_code} ${flight.origin_airport_icao_code}-${flight.destination_airport_icao_code}`
      });
      // Aircraft marker popup disabled: live data is shown in the left Company panel.
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

        showSelectedFlightPath(flight);

        const selectedAircraftDetail = {
          flightInstanceId,
          aircraftId,
          registrationCode: flight.registration_code || flight.registrationCode || null
        };

        if (typeof window.icaroShowAircraftLivePanel === "function") {
          window.icaroShowAircraftLivePanel(selectedAircraftDetail);
        }

        window.dispatchEvent(new CustomEvent("icaro:aircraft-selected", {
          detail: selectedAircraftDetail
        }));
      });

      marker.addTo(icaroFlightLayer);

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
      }
    }
  } catch {
    // Silent for now. The main map must remain usable.
  }
}

function showSelectedFlightPath(flight) {
  if (!window.icaroOpsMap || !icaroFlightLayer) {
    return;
  }

  if (icaroSelectedFlightPathLayer) {
    icaroFlightLayer.removeLayer(icaroSelectedFlightPathLayer);
    icaroSelectedFlightPathLayer = null;
  }

  const origin = [
    Number(flight.origin_latitude),
    Number(flight.origin_longitude)
  ];

  const destination = [
    Number(flight.destination_latitude),
    Number(flight.destination_longitude)
  ];

  if ([...origin, ...destination].some(Number.isNaN)) {
    return;
  }

  icaroSelectedFlightPathLayer = L.polyline([origin, destination], {
    color: "#e53935",
    weight: 4,
    opacity: 0.88,
    dashArray: "8 7",
    lineCap: "round",
    lineJoin: "round"
  }).addTo(icaroFlightLayer);
}

function interpolateFlightPosition(flight) {
  const p = Math.max(0, Math.min(100, Number(flight.progress_percent || 0))) / 100;

  const origin = L.latLng(
    Number(flight.origin_latitude),
    Number(flight.origin_longitude)
  );

  const destination = L.latLng(
    Number(flight.destination_latitude),
    Number(flight.destination_longitude)
  );

  if (
    Number.isNaN(origin.lat) ||
    Number.isNaN(origin.lng) ||
    Number.isNaN(destination.lat) ||
    Number.isNaN(destination.lng) ||
    !window.icaroOpsMap
  ) {
    return null;
  }

  /*
   * Important:
   * Interpolate in Leaflet layer-point space, not directly in lat/lng.
   * This keeps the aircraft marker exactly on the visible route line
   * at the current map zoom/projection.
   */
  const originPoint = window.icaroOpsMap.latLngToLayerPoint(origin);
  const destinationPoint = window.icaroOpsMap.latLngToLayerPoint(destination);

  const currentPoint = L.point(
    originPoint.x + (destinationPoint.x - originPoint.x) * p,
    originPoint.y + (destinationPoint.y - originPoint.y) * p
  );

  const currentLatLng = window.icaroOpsMap.layerPointToLatLng(currentPoint);

  return {
    lat: currentLatLng.lat,
    lng: currentLatLng.lng
  };
}

function aircraftMarkerSvg(bearingDegrees = 0) {
  return `
    <div class="flight-aircraft-marker" style="--flight-bearing: ${Number(bearingDegrees).toFixed(1)}deg">
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path d="M21 16v-2l-8-5V3.5a1.5 1.5 0 0 0-3 0V9l-8 5v2l8-2.5V19l-2 1.5V22l3.5-1 3.5 1v-1.5L13 19v-5.5l8 2.5Z"/>
      </svg>
    </div>
  `;
}

function calculateBearingDegrees(lat1, lon1, lat2, lon2) {
  if ([lat1, lon1, lat2, lon2].some(Number.isNaN)) {
    return 0;
  }

  const phi1 = lat1 * Math.PI / 180;
  const phi2 = lat2 * Math.PI / 180;
  const deltaLambda = (lon2 - lon1) * Math.PI / 180;

  const y = Math.sin(deltaLambda) * Math.cos(phi2);
  const x =
    Math.cos(phi1) * Math.sin(phi2) -
    Math.sin(phi1) * Math.cos(phi2) * Math.cos(deltaLambda);

  const bearing = Math.atan2(y, x) * 180 / Math.PI;
  return (bearing + 360) % 360;
}

function escapeHtmlFlight(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}


function firstDefinedFlight(...values) {
  for (const value of values) {
    if (value !== undefined && value !== null && value !== "") {
      return value;
    }
  }

  return null;
}


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

