(() => {
  const API = {
    activeList: "api/public/flights/active-list.php",
    activeDetailByFlight: id => `api/public/flights/active-detail.php?flight_instance_id=${encodeURIComponent(id)}`
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

  const COMPANY_PANEL_SELECTORS = [
    "#mapSidebar",
    "#dashboardSidebar",
    "#baseSidebar",
    "#companyPanel",
    "#companyInfoPanel",
    "#companyOverview",
    "#leftPanel",
    "#sidebar",
    ".map-sidebar",
    ".dashboard-sidebar",
    ".base-sidebar",
    ".company-panel",
    ".company-overview",
    ".left-panel",
    ".sidebar"
  ];

  const BASE_SELECTORS = [
    "[data-base-id]",
    "[data-airport-base]",
    "[data-company-base]",
    ".base-marker",
    ".hq-marker",
    ".airport-base-marker",
    ".rival-base-marker",
    ".other-player-base-marker"
  ];

  let activeFlights = [];
  let activeFlightByAircraftId = new Map();
  let activeFlightByRegistration = new Map();
  let selectedFlightInstanceId = null;
  let selectedTimerId = null;
  let companyPanelOriginalHtml = null;
  let companyPanelElement = null;

  document.addEventListener("DOMContentLoaded", async () => {
    companyPanelElement = findCompanyPanel();

    if (companyPanelElement && companyPanelOriginalHtml === null) {
      companyPanelOriginalHtml = companyPanelElement.innerHTML;
    }

    await refreshActiveFlights(true);

    window.setInterval(() => refreshActiveFlights(false), 3000);

    bindMapClicks();

    window.icaroShowAircraftLivePanel = async detail => {
      const safeDetail = detail || {};
      const flightInstanceId = safeDetail.flightInstanceId || safeDetail.flight_instance_id;

      if (flightInstanceId) {
        await showFlightInLeftPanel(flightInstanceId);
        return;
      }

      const aircraftId = safeDetail.aircraftId || safeDetail.aircraft_id;

      if (aircraftId && activeFlightByAircraftId.has(String(aircraftId))) {
        const flight = activeFlightByAircraftId.get(String(aircraftId));
        await showFlightInLeftPanel(flight.flight_instance_id);
      }
    };

    window.addEventListener("icaro:aircraft-selected", async event => {
      if (typeof window.icaroShowAircraftLivePanel === "function") {
        await window.icaroShowAircraftLivePanel(event.detail || {});
      }
    });


  window.addEventListener("icaro:aircraft-selected", async event => {
    const detail = event.detail || {};
    const flightInstanceId = detail.flightInstanceId;

    if (flightInstanceId) {
      await showFlightInLeftPanel(flightInstanceId);
      return;
    }

    const aircraftId = detail.aircraftId;

    if (aircraftId && activeFlightByAircraftId.has(String(aircraftId))) {
      const flight = activeFlightByAircraftId.get(String(aircraftId));
      await showFlightInLeftPanel(flight.flight_instance_id);
    }
  });

  });

  async function refreshActiveFlights(firstLoad) {
    try {
      const data = await getJson(API.activeList);
      activeFlights = data.active_flights || [];
      rebuildIndexes();

      tagMapAircraftElements();

      if (firstLoad) {
        injectNoPopupCss();
      }

      if (selectedFlightInstanceId) {
        const stillActive = activeFlights.some(f => String(f.flight_instance_id) === String(selectedFlightInstanceId));

        if (stillActive) {
          await showFlightInLeftPanel(selectedFlightInstanceId, { keepExistingLoading: true });
        }
      }
    } catch (error) {
      console.warn("Unable to refresh active flights", error);
    }
  }

  function rebuildIndexes() {
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
  }

  function bindMapClicks() {
    document.addEventListener("click", async event => {
      const mapRoot = event.target.closest(MAP_SELECTORS.join(","));

      if (!mapRoot) {
        return;
      }

      const base = event.target.closest(BASE_SELECTORS.join(","));

      if (base) {
        restoreCompanyPanel();
        return;
      }

      const flight = findFlightFromClickedElement(event.target);

      if (!flight) {
        return;
      }

      event.preventDefault();
      event.stopPropagation();

      closeMapPopups();

      await showFlightInLeftPanel(flight.flight_instance_id);
    }, true);
  }

  function findCompanyPanel() {
    for (const selector of COMPANY_PANEL_SELECTORS) {
      const el = document.querySelector(selector);

      if (el) {
        return el;
      }
    }

    const main = document.querySelector("main") || document.body;
    let panel = document.querySelector("#aircraftLiveLeftPanel");

    if (!panel) {
      panel = document.createElement("aside");
      panel.id = "aircraftLiveLeftPanel";
      panel.className = "aircraft-live-left-panel";
      main.prepend(panel);
    }

    return panel;
  }

  function restoreCompanyPanel() {
    selectedFlightInstanceId = null;

    if (selectedTimerId) {
      window.clearInterval(selectedTimerId);
      selectedTimerId = null;
    }

    if (!companyPanelElement) {
      companyPanelElement = findCompanyPanel();
    }

    if (companyPanelElement && companyPanelOriginalHtml !== null) {
      companyPanelElement.innerHTML = companyPanelOriginalHtml;
      companyPanelElement.classList.remove("aircraft-live-mode");
    }
  }

  async function showFlightInLeftPanel(flightInstanceId, options = {}) {
    selectedFlightInstanceId = flightInstanceId;

    if (!companyPanelElement) {
      companyPanelElement = findCompanyPanel();
    }

    if (!companyPanelElement) {
      return;
    }

    if (companyPanelOriginalHtml === null) {
      companyPanelOriginalHtml = companyPanelElement.innerHTML;
    }

    companyPanelElement.classList.add("aircraft-live-mode");

    if (!options.keepExistingLoading) {
      companyPanelElement.innerHTML = `
        <section class="aircraft-live-panel-card">
          <p class="eyebrow">Live aircraft</p>
          <h2>Loading aircraft...</h2>
        </section>
      `;
    }

    try {
      const data = await getJson(API.activeDetailByFlight(flightInstanceId));
      renderAircraftLivePanel(data);
    } catch (error) {
      companyPanelElement.innerHTML = `
        <section class="aircraft-live-panel-card">
          <p class="eyebrow">Live aircraft</p>
          <h2>Unable to load aircraft</h2>
          <div class="page-error">${escapeHtml(error.message || "Unable to load live aircraft data.")}</div>
          <button type="button" id="restoreCompanyPanelButton">Back to company</button>
        </section>
      `;

      companyPanelElement.querySelector("#restoreCompanyPanelButton")?.addEventListener("click", restoreCompanyPanel);
    }
  }

  function renderAircraftLivePanel(data) {
    const flight = data.flight;
    const aircraft = data.aircraft;
    const crew = data.crew;

    companyPanelElement.innerHTML = `
      <section class="aircraft-live-panel-card">
        <div class="aircraft-live-panel-header">
          <div>
            <p class="eyebrow">Live aircraft</p>
            <h2>${escapeHtml(aircraft.registration_code)}</h2>
          </div>
        </div>

        <div class="aircraft-live-model">
          <strong>${escapeHtml(aircraft.icao_type_code || aircraft.model_code || "-")}</strong>
          <span>${escapeHtml(aircraft.manufacturer || "")} ${escapeHtml(aircraft.model_name || "")}</span>
        </div>

        <dl class="aircraft-live-list">
          ${row("Flight", flight.flight_code)}
          ${row("Route", `${flight.origin_airport_icao_code} → ${flight.destination_airport_icao_code}`)}
          ${row("Status", flight.status)}
          ${row("Speed", `${aircraft.cruise_speed_kmh || "-"} km/h`)}
          ${row("Departure UTC", flight.actual_departure_at_utc || "-")}
          ${row("Arrival UTC", flight.scheduled_arrival_at_utc || "-")}
          ${row("Remaining", `<span id="leftPanelLiveRemaining">-</span>`)}
          ${row("Progress", `<span id="leftPanelLiveProgress">-</span>`)}
          ${row("Passengers", `${flight.passenger_count} / ${flight.passenger_capacity}`)}
          ${flightProfitRow(flight)}
</dl>
      </section>
    `;

    bindProfitDialog(flight);
    startPanelTimer(flight);
  }

  function startPanelTimer(flight) {
    if (selectedTimerId) {
      window.clearInterval(selectedTimerId);
      selectedTimerId = null;
    }

    const remainingEl = companyPanelElement.querySelector("#leftPanelLiveRemaining");
    const progressEl = companyPanelElement.querySelector("#leftPanelLiveProgress");

    const departureTs = parseUtc(flight.actual_departure_at_utc);
    const arrivalTs = parseUtc(flight.scheduled_arrival_at_utc);

    const tick = () => {
      if (!remainingEl || !progressEl || !document.body.contains(remainingEl)) {
        if (selectedTimerId) {
          window.clearInterval(selectedTimerId);
          selectedTimerId = null;
        }
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

        if (selectedTimerId) {
          window.clearInterval(selectedTimerId);
          selectedTimerId = null;
        }
      }
    };

    tick();
    selectedTimerId = window.setInterval(tick, 1000);
  }

  function tagMapAircraftElements() {
    const mapRoots = MAP_SELECTORS.flatMap(selector => Array.from(document.querySelectorAll(selector)));

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
            element.title = "Click to show aircraft live status";
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

    const text = target.closest("*")?.textContent || "";

    for (const [registration, flight] of activeFlightByRegistration.entries()) {
      if (text.includes(registration)) {
        return flight;
      }
    }

    return null;
  }

  function closeMapPopups() {
    document.querySelectorAll(".leaflet-popup, .map-popup, .aircraft-popup, .flight-popup, [data-map-popup]").forEach(popup => {
      popup.remove();
    });

    document.querySelectorAll(".leaflet-popup-pane").forEach(pane => {
      pane.innerHTML = "";
    });
  }

  function injectNoPopupCss() {
    if (document.querySelector("#icaroNoAircraftPopupCss")) {
      return;
    }

    const style = document.createElement("style");
    style.id = "icaroNoAircraftPopupCss";
    style.textContent = `
      .leaflet-popup:has(.aircraft-popup),
      .leaflet-popup:has(.flight-popup) {
        display: none !important;
      }
    `;
    document.head.appendChild(style);
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


  function cleanText(value) {
    const text = String(value ?? "").trim();

    if (!text || text.toLowerCase() === "null" || text.toLowerCase() === "undefined") {
      return "-";
    }

    return escapeHtml(text);
  }

  function flightProfitRow(flight) {
    const currency = escapeHtml(flight.currency_code || "EUR");
    const profit = Number(flight.profit_amount || 0);
    const cssClass = profitClass(profit);
    const label = profit > 0 ? "Profit" : profit < 0 ? "Loss" : "Break-even";

    return row(
      "Profit",
      `<button type="button" id="leftPanelProfitButton" class="aircraft-live-profit-button ${cssClass}" title="Show flight economic details">${label}: ${money(profit)} ${currency}</button>`
    );
  }

  function profitClass(value) {
    const n = Number(value || 0);

    if (n > 0) {
      return "profit-positive";
    }

    if (n < 0) {
      return "profit-negative";
    }

    return "";
  }

  function money(value) {
    const n = Number(value || 0);

    return n.toLocaleString(undefined, {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    });
  }

function row(label, value) {
    return `<div><dt>${escapeHtml(label)}</dt><dd>${value}</dd></div>`;
  }

  function bindProfitDialog(flight) {
    const button = companyPanelElement?.querySelector("#leftPanelProfitButton");

    if (!button) {
      return;
    }

    button.addEventListener("click", () => showFlightProfitDialog(flight));
  }

  function showFlightProfitDialog(flight) {
    const currency = escapeHtml(flight.currency_code || "EUR");
    const profit = Number(flight.profit_amount || 0);
    const revenue = Number(flight.passenger_revenue || 0);
    const cost = Number(flight.total_operating_cost || 0);
    const cssClass = profitClass(profit);
    const label = profit > 0 ? "Profit" : profit < 0 ? "Loss" : "Break-even";

    injectProfitDialogCss();

    const dialog = document.createElement("dialog");
    dialog.className = "aircraft-live-profit-dialog";
    dialog.innerHTML = `
      <form method="dialog" class="aircraft-live-profit-dialog-card">
        <header>
          <div>
            <p class="eyebrow">Flight economics</p>
            <h2>${escapeHtml(flight.flight_code || "Flight")}</h2>
          </div>
          <button type="submit" aria-label="Close">×</button>
        </header>

        <dl>
          ${row("Route", `${escapeHtml(flight.origin_airport_icao_code || "-")} → ${escapeHtml(flight.destination_airport_icao_code || "-")}`)}
          ${row("Passengers", `${escapeHtml(flight.passenger_count ?? "-")} / ${escapeHtml(flight.passenger_capacity ?? "-")}`)}
          ${row("Revenue", `${money(revenue)} ${currency}`)}
          ${row("Operating cost", `${money(cost)} ${currency}`)}
          ${row(label, `<strong class="${cssClass}">${money(profit)} ${currency}</strong>`)}
        </dl>
      </form>
    `;

    document.body.appendChild(dialog);
    dialog.addEventListener("close", () => dialog.remove(), { once: true });

    if (typeof dialog.showModal === "function") {
      dialog.showModal();
      return;
    }

    window.alert(`${label}: ${money(profit)} ${currency}
Revenue: ${money(revenue)} ${currency}
Cost: ${money(cost)} ${currency}`);
    dialog.remove();
  }

  function injectProfitDialogCss() {
    if (document.querySelector("#icaroLiveAircraftProfitDialogCss")) {
      return;
    }

    const style = document.createElement("style");
    style.id = "icaroLiveAircraftProfitDialogCss";
    style.textContent = `
      .aircraft-live-profit-button {
        border: 0;
        padding: 0;
        background: transparent;
        font: inherit;
        font-weight: 700;
        cursor: pointer;
        text-decoration: underline;
        text-underline-offset: 0.15em;
      }

      .aircraft-live-profit-dialog::backdrop {
        background: rgba(0, 0, 0, 0.45);
      }

      .aircraft-live-profit-dialog {
        border: 0;
        border-radius: 16px;
        padding: 0;
        max-width: min(520px, 92vw);
      }

      .aircraft-live-profit-dialog-card {
        padding: 1.25rem;
        min-width: min(420px, 86vw);
      }

      .aircraft-live-profit-dialog-card header {
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        gap: 1rem;
        margin-bottom: 1rem;
      }

      .aircraft-live-profit-dialog-card header button {
        border: 0;
        background: transparent;
        font-size: 1.5rem;
        cursor: pointer;
      }

      .aircraft-live-profit-dialog-card dl {
        display: grid;
        gap: 0.6rem;
        margin: 0;
      }

      .aircraft-live-profit-dialog-card dl > div {
        display: grid;
        grid-template-columns: 1fr auto;
        gap: 1rem;
        align-items: baseline;
      }

      .aircraft-live-profit-dialog-card dt,
      .aircraft-live-profit-dialog-card dd {
        margin: 0;
      }
    `;
    document.head.appendChild(style);
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

  function escapeHtml(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }
})();
