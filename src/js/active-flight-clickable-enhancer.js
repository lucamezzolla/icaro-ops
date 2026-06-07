(() => {
  const API = {
    activeList: "api/public/flights/active-list.php"
  };

  let activeFlights = [];
  let refreshTimerId = null;

  document.addEventListener("DOMContentLoaded", () => {
    refreshActiveFlights();
    refreshTimerId = window.setInterval(refreshActiveFlights, 5000);
  });

  async function refreshActiveFlights() {
    try {
      const data = await getJson(API.activeList);
      activeFlights = data.active_flights || [];

      renderActiveFlightsPanel(activeFlights);
      makeExistingAircraftRowsClickable(activeFlights);
    } catch (error) {
      console.warn("Unable to refresh active flights", error);
    }
  }

  function renderActiveFlightsPanel(flights) {
    let panel = document.querySelector("#activeFlightsQuickPanel");

    if (!flights.length) {
      if (panel) {
        panel.remove();
      }
      return;
    }

    if (!panel) {
      panel = document.createElement("aside");
      panel.id = "activeFlightsQuickPanel";
      panel.innerHTML = `
        <header>
          <strong>Active flights</strong>
          <button type="button" id="activeFlightsQuickPanelClose" aria-label="Close">×</button>
        </header>
        <div id="activeFlightsQuickPanelBody"></div>
      `;
      document.body.appendChild(panel);

      panel.querySelector("#activeFlightsQuickPanelClose").addEventListener("click", () => {
        panel.hidden = true;
      });
    }

    const body = panel.querySelector("#activeFlightsQuickPanelBody");

    body.innerHTML = flights.map(flight => `
      <button
        type="button"
        class="active-flight-chip"
        data-flight-instance-id="${escapeHtml(flight.flight_instance_id)}"
        data-aircraft-id="${escapeHtml(flight.aircraft_id)}"
      >
        <span>
          <strong>${escapeHtml(flight.registration_code)}</strong>
          ${escapeHtml(flight.icao_type_code || flight.model_code || "")}
        </span>
        <small>
          ${escapeHtml(flight.origin_airport_icao_code)} → ${escapeHtml(flight.destination_airport_icao_code)}
          · ${escapeHtml(flight.cruise_speed_kmh || "-")} km/h
          · ${formatSeconds(Number(flight.remaining_seconds || 0))}
        </small>
      </button>
    `).join("");

    body.querySelectorAll("[data-flight-instance-id]").forEach(button => {
      button.addEventListener("click", () => {
        openActiveFlightDialogFromEnhancer(button.dataset.flightInstanceId);
      });
    });

    panel.hidden = false;
  }

  function makeExistingAircraftRowsClickable(flights) {
    for (const flight of flights) {
      const registration = String(flight.registration_code || "").trim();

      if (!registration) {
        continue;
      }

      const candidates = Array.from(document.querySelectorAll("tr, .fleet-card, .aircraft-card, .aircraft-row, .vehicle-card, li, article, section"))
        .filter(element => element.textContent && element.textContent.includes(registration));

      for (const element of candidates) {
        element.dataset.aircraftId = flight.aircraft_id;
        element.dataset.flightInstanceId = flight.flight_instance_id;
        element.classList.add("active-flight-clickable");

        if (!element.dataset.activeFlightEnhancerBound) {
          element.dataset.activeFlightEnhancerBound = "true";
          element.title = "Click to view live speed and remaining time";

          element.addEventListener("click", event => {
            const interactive = event.target.closest("button, a, input, select, textarea, label");

            if (interactive && interactive !== element) {
              return;
            }

            openActiveFlightDialogFromEnhancer(flight.flight_instance_id);
          });
        }
      }
    }
  }

  async function openActiveFlightDialogFromEnhancer(flightInstanceId) {
    const dialog = ensureActiveFlightDialog();
    const title = dialog.querySelector("#activeFlightTitle");
    const body = dialog.querySelector("#activeFlightBody");

    title.textContent = "Active flight";
    body.innerHTML = `<p class="muted">Loading active flight...</p>`;
    dialog.showModal();

    try {
      const data = await getJson(`api/public/flights/active-detail.php?flight_instance_id=${encodeURIComponent(flightInstanceId)}`);
      renderActiveFlight(dialog, data);
    } catch (error) {
      body.innerHTML = `<div class="page-error">${escapeHtml(error.message || "Unable to load active flight.")}</div>`;
    }
  }

  function renderActiveFlight(dialog, data) {
    const title = dialog.querySelector("#activeFlightTitle");
    const body = dialog.querySelector("#activeFlightBody");

    const flight = data.flight;
    const aircraft = data.aircraft;
    const crew = data.crew;

    title.textContent = `${flight.flight_code} · ${aircraft.registration_code}`;

    body.innerHTML = `
      <div class="detail-grid">
        <section class="detail-section">
          <h3>Flight</h3>
          <dl class="detail-list">
            ${detailRow("Route", `${escapeHtml(flight.origin_airport_icao_code)} → ${escapeHtml(flight.destination_airport_icao_code)}`)}
            ${detailRow("Status", escapeHtml(flight.status))}
            ${detailRow("Dispatch", escapeHtml(flight.dispatch_status))}
            ${detailRow("Departure UTC", escapeHtml(flight.actual_departure_at_utc || "-"))}
            ${detailRow("Estimated arrival UTC", escapeHtml(flight.scheduled_arrival_at_utc || "-"))}
            ${detailRow("Remaining", `<span id="activeFlightRemaining">-</span>`)}
            ${detailRow("Progress", `<span id="activeFlightProgress">-</span>`)}
          </dl>
        </section>

        <section class="detail-section">
          <h3>Aircraft</h3>
          <dl class="detail-list">
            ${detailRow("Registration", escapeHtml(aircraft.registration_code))}
            ${detailRow("Type", `${escapeHtml(aircraft.icao_type_code || "-")} · ${escapeHtml(aircraft.manufacturer || "")} ${escapeHtml(aircraft.model_name || "")}`)}
            ${detailRow("Speed", `${escapeHtml(aircraft.cruise_speed_kmh || "-")} km/h estimated cruise`)}
            ${detailRow("Current airport", escapeHtml(aircraft.current_airport_icao_code || "-"))}
            ${detailRow("Passengers", `${escapeHtml(flight.passenger_count)} / ${escapeHtml(flight.passenger_capacity)}`)}
          </dl>
        </section>

        <section class="detail-section">
          <h3>Crew</h3>
          <dl class="detail-list">
            ${detailRow("Pilot 1", escapeHtml(crew.pilot_1_name || "-"))}
            ${detailRow("Pilot 2", escapeHtml(crew.pilot_2_name || "-"))}
          </dl>
        </section>
      </div>
    `;

    startRemainingTimer(dialog, flight);
  }

  function startRemainingTimer(dialog, flight) {
    if (dialog.activeTimerId) {
      window.clearInterval(dialog.activeTimerId);
    }

    const remainingEl = dialog.querySelector("#activeFlightRemaining");
    const progressEl = dialog.querySelector("#activeFlightProgress");

    const arrivalTs = parseUtc(flight.scheduled_arrival_at_utc);
    const departureTs = parseUtc(flight.actual_departure_at_utc);

    const tick = () => {
      const now = Date.now();

      if (!arrivalTs || !departureTs || arrivalTs <= departureTs) {
        remainingEl.textContent = "-";
        progressEl.textContent = "-";
        return;
      }

      const remainingMs = Math.max(0, arrivalTs - now);
      const totalMs = arrivalTs - departureTs;
      const elapsedMs = Math.max(0, now - departureTs);
      const progress = Math.max(0, Math.min(100, (elapsedMs / totalMs) * 100));

      remainingEl.textContent = formatMilliseconds(remainingMs);
      progressEl.textContent = `${progress.toFixed(1)}%`;

      if (remainingMs <= 0) {
        remainingEl.textContent = "Arriving / completed";
        window.clearInterval(dialog.activeTimerId);
        dialog.activeTimerId = null;
      }
    };

    tick();
    dialog.activeTimerId = window.setInterval(tick, 1000);

    dialog.addEventListener("close", () => {
      if (dialog.activeTimerId) {
        window.clearInterval(dialog.activeTimerId);
        dialog.activeTimerId = null;
      }
    }, { once: true });
  }

  function ensureActiveFlightDialog() {
    let dialog = document.querySelector("#activeFlightDialog");

    if (dialog) {
      return dialog;
    }

    dialog = document.createElement("dialog");
    dialog.id = "activeFlightDialog";
    dialog.innerHTML = `
      <form method="dialog" class="dialog-card">
        <header class="dialog-header">
          <div>
            <p class="eyebrow">Live aircraft</p>
            <h2 id="activeFlightTitle">Active flight</h2>
          </div>
          <button type="button" class="close-button" aria-label="Close">×</button>
        </header>
        <div id="activeFlightBody" class="dialog-body"></div>
        <footer class="dialog-footer">
          <button value="close">Close</button>
        </footer>
      </form>
    `;

    dialog.querySelector(".close-button").addEventListener("click", () => dialog.close());
    document.body.appendChild(dialog);

    return dialog;
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

  function parseUtc(value) {
    if (!value) {
      return null;
    }

    return new Date(`${String(value).replace(" ", "T")}Z`).getTime();
  }

  function formatMilliseconds(ms) {
    const totalSeconds = Math.max(0, Math.floor(ms / 1000));
    return formatSeconds(totalSeconds);
  }

  function formatSeconds(totalSeconds) {
    const safeSeconds = Math.max(0, Number(totalSeconds || 0));
    const hours = Math.floor(safeSeconds / 3600);
    const minutes = Math.floor((safeSeconds % 3600) / 60);
    const seconds = Math.floor(safeSeconds % 60);

    return `${String(hours).padStart(2, "0")}:${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;
  }

  function detailRow(label, value) {
    return `<div><dt>${escapeHtml(label)}</dt><dd>${value}</dd></div>`;
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
