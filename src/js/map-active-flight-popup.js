(() => {
  const API = {
    activeList: "api/public/flights/active-list.php",
    activeDetailByFlight: id => `api/public/flights/active-detail.php?flight_instance_id=${encodeURIComponent(id)}`,
    activeDetailByAircraft: id => `api/public/flights/active-detail.php?aircraft_id=${encodeURIComponent(id)}`
  };

  const MAP_SELECTORS = [
    "#map",
    "#worldMap",
    "#flightMap",
    "#operationsMap",
    "#dashboardMap",
    ".map",
    ".leaflet-container",
    "[data-map]"
  ];

  const POPUP_SELECTORS = [
    ".leaflet-popup-content",
    ".map-popup",
    ".aircraft-popup",
    ".flight-popup",
    ".popup-content",
    "[data-map-popup]",
    "[role='tooltip']"
  ];

  let activeFlights = [];
  let activeFlightByAircraftId = new Map();
  let activeFlightByRegistration = new Map();
  let popupTimerId = null;

  document.addEventListener("DOMContentLoaded", async () => {
    await refreshActiveFlights();
    window.setInterval(refreshActiveFlights, 5000);
    bindMapClickListener();
  });

  async function refreshActiveFlights() {
    try {
      const data = await getJson(API.activeList);
      activeFlights = data.active_flights || [];

      activeFlightByAircraftId = new Map();
      activeFlightByRegistration = new Map();

      for (const flight of activeFlights) {
        if (flight.aircraft_id !== undefined && flight.aircraft_id !== null) {
          activeFlightByAircraftId.set(String(flight.aircraft_id), flight);
        }

        if (flight.registration_code) {
          activeFlightByRegistration.set(String(flight.registration_code), flight);
        }
      }

      tagMapAircraftElements();
    } catch (error) {
      console.warn("Unable to refresh active map flights", error);
    }
  }

  function bindMapClickListener() {
    document.addEventListener("click", async event => {
      const mapRoot = event.target.closest(MAP_SELECTORS.join(","));

      if (!mapRoot) {
        return;
      }

      const flight = findFlightFromClickedElement(event.target);

      if (!flight) {
        return;
      }

      window.setTimeout(async () => {
        await injectLiveDataIntoCurrentMapPopup(flight);
      }, 80);

      window.setTimeout(async () => {
        await injectLiveDataIntoCurrentMapPopup(flight);
      }, 250);
    }, true);
  }

  function tagMapAircraftElements() {
    const mapRoots = MAP_SELECTORS
      .flatMap(selector => Array.from(document.querySelectorAll(selector)));

    if (!mapRoots.length || !activeFlights.length) {
      return;
    }

    for (const root of mapRoots) {
      const candidates = Array.from(root.querySelectorAll("*"));

      for (const element of candidates) {
        const text = element.textContent || "";

        for (const flight of activeFlights) {
          if (!flight.registration_code) {
            continue;
          }

          if (text.includes(flight.registration_code)) {
            element.dataset.aircraftId = flight.aircraft_id;
            element.dataset.flightInstanceId = flight.flight_instance_id;
            element.classList.add("map-aircraft-live-target");
            element.title = "Click to show live flight data";
          }
        }
      }
    }
  }

  function findFlightFromClickedElement(target) {
    const element = target.closest("[data-flight-instance-id], [data-aircraft-id], .aircraft-marker, .flight-aircraft-marker, .map-aircraft-live-target");

    if (element) {
      const flightInstanceId = element.dataset.flightInstanceId;
      const aircraftId = element.dataset.aircraftId;

      if (flightInstanceId) {
        const byFlight = activeFlights.find(f => String(f.flight_instance_id) === String(flightInstanceId));

        if (byFlight) {
          return byFlight;
        }
      }

      if (aircraftId && activeFlightByAircraftId.has(String(aircraftId))) {
        return activeFlightByAircraftId.get(String(aircraftId));
      }
    }

    const clickedText = target.closest("*")?.textContent || "";

    for (const [registration, flight] of activeFlightByRegistration.entries()) {
      if (clickedText.includes(registration)) {
        return flight;
      }
    }

    return null;
  }

  async function injectLiveDataIntoCurrentMapPopup(flightSummary) {
    const popup = findCurrentPopup();

    if (!popup) {
      return;
    }

    const existing = popup.querySelector("#mapAircraftLiveBox");

    if (existing) {
      existing.remove();
    }

    const box = document.createElement("section");
    box.id = "mapAircraftLiveBox";
    box.className = "map-aircraft-live-box";
    box.innerHTML = `<p class="muted">Loading live aircraft data...</p>`;
    popup.appendChild(box);

    try {
      const data = await getJson(API.activeDetailByFlight(flightSummary.flight_instance_id));
      renderLiveBox(box, data);
    } catch (error) {
      box.innerHTML = `<div class="page-error">${escapeHtml(error.message || "Unable to load live aircraft data.")}</div>`;
    }
  }

  function findCurrentPopup() {
    for (const selector of POPUP_SELECTORS) {
      const popups = Array.from(document.querySelectorAll(selector))
        .filter(el => isVisible(el));

      if (popups.length) {
        return popups[popups.length - 1];
      }
    }

    return null;
  }

  function renderLiveBox(box, data) {
    const flight = data.flight;
    const aircraft = data.aircraft;
    const crew = data.crew;

    box.innerHTML = `
      <div class="map-live-title">
        <strong>${escapeHtml(aircraft.registration_code)}</strong>
        <span>${escapeHtml(aircraft.icao_type_code || aircraft.model_code || "")}</span>
      </div>

      <dl class="map-live-list">
        ${row("Flight", flight.flight_code)}
        ${row("Route", `${flight.origin_airport_icao_code} → ${flight.destination_airport_icao_code}`)}
        ${row("Speed", `${aircraft.cruise_speed_kmh || "-"} km/h`)}
        ${row("Remaining", `<span id="mapLiveRemaining">-</span>`)}
        ${row("Progress", `<span id="mapLiveProgress">-</span>`)}
        ${row("Arrival UTC", flight.scheduled_arrival_at_utc || "-")}
        ${row("Crew", `${crew.pilot_1_name || "-"} / ${crew.pilot_2_name || "-"}`)}
      </dl>
    `;

    startPopupTimer(flight);
  }

  function startPopupTimer(flight) {
    if (popupTimerId) {
      window.clearInterval(popupTimerId);
      popupTimerId = null;
    }

    const remainingEl = document.querySelector("#mapLiveRemaining");
    const progressEl = document.querySelector("#mapLiveProgress");

    if (!remainingEl || !progressEl) {
      return;
    }

    const departureTs = parseUtc(flight.actual_departure_at_utc);
    const arrivalTs = parseUtc(flight.scheduled_arrival_at_utc);

    const tick = () => {
      if (!document.body.contains(remainingEl)) {
        window.clearInterval(popupTimerId);
        popupTimerId = null;
        return;
      }

      if (!departureTs || !arrivalTs || arrivalTs <= departureTs) {
        remainingEl.textContent = "-";
        progressEl.textContent = "-";
        return;
      }

      const now = Date.now();
      const remainingMs = Math.max(0, arrivalTs - now);
      const totalMs = arrivalTs - departureTs;
      const elapsedMs = Math.max(0, now - departureTs);
      const progress = Math.max(0, Math.min(100, (elapsedMs / totalMs) * 100));

      remainingEl.textContent = formatDuration(remainingMs);
      progressEl.textContent = `${progress.toFixed(1)}%`;

      if (remainingMs <= 0) {
        remainingEl.textContent = "Arriving / completed";
        window.clearInterval(popupTimerId);
        popupTimerId = null;
      }
    };

    tick();
    popupTimerId = window.setInterval(tick, 1000);
  }

  async function getJson(url) {
    const response = await fetch(url, {
      headers: { "Accept": "application/json" },
      credentials: "same-origin"
    });

    const body = await response.json().catch(() => null);

    if (!response.ok) {
      throw new Error(body?.message || body?.error || `Request failed: ${response.status}`);
    }

    return body;
  }

  function row(label, value) {
    return `<div><dt>${escapeHtml(label)}</dt><dd>${value}</dd></div>`;
  }

  function parseUtc(value) {
    if (!value) {
      return null;
    }

    return new Date(`${String(value).replace(" ", "T")}Z`).getTime();
  }

  function formatDuration(ms) {
    const totalSeconds = Math.max(0, Math.floor(ms / 1000));
    const hours = Math.floor(totalSeconds / 3600);
    const minutes = Math.floor((totalSeconds % 3600) / 60);
    const seconds = totalSeconds % 60;

    return `${String(hours).padStart(2, "0")}:${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;
  }

  function isVisible(element) {
    const rect = element.getBoundingClientRect();
    const style = window.getComputedStyle(element);

    return rect.width > 0 &&
      rect.height > 0 &&
      style.display !== "none" &&
      style.visibility !== "hidden";
  }

  function escapeHtml(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }
})();
