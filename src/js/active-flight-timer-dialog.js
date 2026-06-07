(() => {
  const API = {
    activeFlight: params => `api/public/flights/active-detail.php?${params}`
  };

  document.addEventListener("click", async event => {
    const target = event.target.closest("[data-flight-instance-id], [data-aircraft-id], .aircraft-marker, .flight-aircraft-marker");

    if (!target) {
      return;
    }

    const flightInstanceId = target.dataset.flightInstanceId;
    const aircraftId = target.dataset.aircraftId;

    if (!flightInstanceId && !aircraftId) {
      return;
    }

    event.preventDefault();

    const params = flightInstanceId
      ? `flight_instance_id=${encodeURIComponent(flightInstanceId)}`
      : `aircraft_id=${encodeURIComponent(aircraftId)}`;

    await openActiveFlightDialog(params);
  });

  async function openActiveFlightDialog(params) {
    const dialog = ensureActiveFlightDialog();
    const title = dialog.querySelector("#activeFlightTitle");
    const body = dialog.querySelector("#activeFlightBody");

    title.textContent = "Active flight";
    body.innerHTML = `<p class="muted">Loading active flight...</p>`;
    dialog.showModal();

    try {
      const data = await getJson(API.activeFlight(params));
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
            ${detailRow("Route", `${flight.origin_airport_icao_code} → ${flight.destination_airport_icao_code}`)}
            ${detailRow("Status", flight.status)}
            ${detailRow("Dispatch", flight.dispatch_status)}
            ${detailRow("Departure UTC", flight.actual_departure_at_utc || "-")}
            ${detailRow("Estimated arrival UTC", flight.scheduled_arrival_at_utc || "-")}
            ${detailRow("Remaining", `<span id="activeFlightRemaining">-</span>`)}
            ${detailRow("Progress", `<span id="activeFlightProgress">-</span>`)}
          </dl>
        </section>

        <section class="detail-section">
          <h3>Aircraft</h3>
          <dl class="detail-list">
            ${detailRow("Registration", aircraft.registration_code)}
            ${detailRow("Type", `${aircraft.icao_type_code || "-"} · ${aircraft.manufacturer || ""} ${aircraft.model_name || ""}`)}
            ${detailRow("Speed", `${aircraft.cruise_speed_kmh || "-"} km/h estimated cruise`)}
            ${detailRow("Current airport", aircraft.current_airport_icao_code || "-")}
            ${detailRow("Passengers", `${flight.passenger_count} / ${flight.passenger_capacity}`)}
          </dl>
        </section>

        <section class="detail-section">
          <h3>Crew</h3>
          <dl class="detail-list">
            ${detailRow("Pilot 1", crew.pilot_1_name || "-")}
            ${detailRow("Pilot 2", crew.pilot_2_name || "-")}
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

      remainingEl.textContent = formatDuration(remainingMs);
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

  function formatDuration(ms) {
    const totalSeconds = Math.max(0, Math.floor(ms / 1000));
    const hours = Math.floor(totalSeconds / 3600);
    const minutes = Math.floor((totalSeconds % 3600) / 60);
    const seconds = totalSeconds % 60;

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
