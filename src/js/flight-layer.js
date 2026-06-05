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
let icaroSelectedFlightPathLayer = null;

document.addEventListener("DOMContentLoaded", () => {
  setTimeout(initIcaroFlightLayer, 500);
});

function initIcaroFlightLayer() {
  if (!window.icaroOpsMap || typeof L === "undefined") {
    return;
  }

  icaroFlightLayer = L.layerGroup().addTo(window.icaroOpsMap);

  refreshIcaroFlights();
  setInterval(refreshIcaroFlights, 15000);
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
          className: "",
          html: aircraftMarkerSvg(),
          iconSize: [34, 34],
          iconAnchor: [17, 17],
          popupAnchor: [0, -16]
        }),
        title: `${flight.flight_code} ${flight.origin_airport_icao_code}-${flight.destination_airport_icao_code}`
      });

      marker.bindPopup(`
        <div class="base-popup">
          <h3>${escapeHtmlFlight(flight.flight_code)}</h3>
          <p><strong>${escapeHtmlFlight(flight.registration_code)}</strong> · ${escapeHtmlFlight(flight.model_name)}</p>
          <p>${escapeHtmlFlight(flight.origin_airport_icao_code)} → ${escapeHtmlFlight(flight.destination_airport_icao_code)}</p>
          <p>Passengers: ${flight.passenger_count}/${flight.passenger_capacity}</p>
          <p>Progress: ${Math.round(Number(flight.progress_percent || 0))}%</p>
          <p>Estimated profit: ${flight.profit_amount} ${flight.currency_code}</p>
        </div>
      `);

      marker.on("click", () => {
        showSelectedFlightPath(flight);
      });

      marker.addTo(icaroFlightLayer);
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

  const oLat = Number(flight.origin_latitude);
  const oLng = Number(flight.origin_longitude);
  const dLat = Number(flight.destination_latitude);
  const dLng = Number(flight.destination_longitude);

  if ([oLat, oLng, dLat, dLng].some(Number.isNaN)) {
    return null;
  }

  return {
    lat: oLat + (dLat - oLat) * p,
    lng: oLng + (dLng - oLng) * p
  };
}

function aircraftMarkerSvg() {
  return `
    <div class="flight-aircraft-marker">
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path d="M21 16v-2l-8-5V3.5a1.5 1.5 0 0 0-3 0V9l-8 5v2l8-2.5V19l-2 1.5V22l3.5-1 3.5 1v-1.5L13 19v-5.5l8 2.5Z"/>
      </svg>
    </div>
  `;
}

function escapeHtmlFlight(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}
