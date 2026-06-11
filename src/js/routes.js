const API = {
  routes: "api/public/routes/list.php",
  create: "api/public/routes/create.php",
  detail: id => `api/public/routes/detail.php?serviceId=${encodeURIComponent(id)}`,
  preview: "api/public/routes/preview.php",
  startServiceFlight: "api/public/flights/start-service-now.php",
  processDueRoutes: "api/public/dispatch/process-due-routes.php",
  removeService: "api/public/routes/delete.php",
  aircraftByIcao: code => `api/public/fleet/model-by-icao.php?icao=${encodeURIComponent(code)}`,
  availableAircraft: id => `api/public/flights/available-aircraft.php?service_id=${encodeURIComponent(id)}`,
  ownedAircraftModels: "api/public/fleet/owned-models.php"
};

let flights = [];
let flightFiltersApplied = false;
let lastSuggestedTicketPrice = null;

document.addEventListener("DOMContentLoaded", async () => {
  startUtcClock();

  document.querySelector("#refreshButton")?.addEventListener("click", loadFlights);
  document.querySelector("#addRouteButton")?.addEventListener("click", openAddFlightDialog);
  document.querySelector("#previewRouteButton")?.addEventListener("click", previewFlight);
  document.querySelector("#saveRouteButton")?.addEventListener("click", saveFlight);

  setupFlightTypeToggle();
  setupFlightTypeExplanation();
  setupTicketSuggestion();
  setupDialogCloseButtons();
  setupFlightFilters();

  await loadFlights();
});

async function loadFlights() {
  hideError();

  try {
    await processDueScheduledFlights();
    flights = await getJson(API.routes);
    renderSummary(flights);
    renderFlights(getVisibleFlightsForCurrentFilters());
  } catch (error) {
    showError(error.message || "Unable to load flights.");
  }
}

async function processDueScheduledFlights() {
  try {
    await postJson(API.processDueRoutes, {
      window_minutes: 120
    });
  } catch (error) {
    console.warn("Unable to process due scheduled flights.", error);
  }
}

function renderSummary(rows) {
  const active = rows.filter(row => row.status === "ACTIVE").length;
  const operated = rows.reduce((total, row) => total + Number(row.generated_flights_count || 0), 0);

  document.querySelector("#routesSummary").innerHTML = `
    ${summaryRow("Flights", rows.length)}
    ${summaryRow("Active", active)}
    ${summaryRow("Operated", operated)}
  `;
}

function setupFlightFilters() {
  if (document.querySelector("#flightTableFilters")) {
    return;
  }

  const table = document.querySelector("#routesTableBody")?.closest("table");
  if (!table) {
    return;
  }

  const filters = document.createElement("section");
  filters.id = "flightTableFilters";
  filters.className = "aircraft-market-filter-panel flight-filter-panel";
  filters.setAttribute("aria-label", "Flight filters");
  filters.innerHTML = `
    <div class="aircraft-market-filters flight-filters">
      <label>
        <span>Departure</span>
        <input type="text" id="flightDepartureFilter" placeholder="ICAO, city, airport">
      </label>

      <label>
        <span>Arrival</span>
        <input type="text" id="flightArrivalFilter" placeholder="ICAO, city, airport">
      </label>

      <label>
        <span>Airplane</span>
        <input type="text" id="flightAirplaneFilter" placeholder="ICAO type code">
      </label>

      <label>
        <span>Scheduled</span>
        <select id="flightScheduledFilter">
          <option value="">Any</option>
          <option value="SCHEDULED">Scheduled</option>
          <option value="ON_DEMAND">On demand</option>
        </select>
      </label>

      <button type="button" id="clearFlightFiltersButton" class="secondary" title="Clear flight filters">🧹 Clear</button>
    </div>

    <p class="muted aircraft-market-filter-summary" id="flightFilterSummary">
      Showing 0 of 0 flights.
    </p>
  `;

  table.parentNode.insertBefore(filters, table);

  ["#flightDepartureFilter", "#flightArrivalFilter", "#flightAirplaneFilter"].forEach(selector => {
    filters.querySelector(selector)?.addEventListener("input", applyFlightFiltersLive);
  });

  filters.querySelector("#flightScheduledFilter")?.addEventListener("change", applyFlightFiltersLive);

  filters.querySelector("#clearFlightFiltersButton")?.addEventListener("click", () => {
    flightFiltersApplied = false;
    filters.querySelector("#flightDepartureFilter").value = "";
    filters.querySelector("#flightArrivalFilter").value = "";
    filters.querySelector("#flightAirplaneFilter").value = "";
    filters.querySelector("#flightScheduledFilter").value = "";
    renderFlights([]);
  });

  updateFlightFilterSummary(0);
}


function updateFlightFilterSummary(visibleCount = 0) {
  const summary = document.querySelector("#flightFilterSummary");
  if (!summary) {
    return;
  }

  summary.textContent = `Showing ${visibleCount} of ${flights.length} flights.`;
}

function applyFlightFiltersLive() {
  flightFiltersApplied = hasActiveFlightFilters();
  renderFlights(getVisibleFlightsForCurrentFilters());
}

function hasActiveFlightFilters() {
  return Boolean(
    normalizedFilterValue("#flightDepartureFilter") ||
    normalizedFilterValue("#flightArrivalFilter") ||
    normalizedFilterValue("#flightAirplaneFilter") ||
    String(document.querySelector("#flightScheduledFilter")?.value || "").trim()
  );
}

function getVisibleFlightsForCurrentFilters() {
  if (!flightFiltersApplied || !hasActiveFlightFilters()) {
    return [];
  }

  const departure = normalizedFilterValue("#flightDepartureFilter");
  const arrival = normalizedFilterValue("#flightArrivalFilter");
  const airplane = normalizedFilterValue("#flightAirplaneFilter");
  const scheduled = String(document.querySelector("#flightScheduledFilter")?.value || "").toUpperCase();

  return flights.filter(flight => {
    if (departure && !flightDepartureSearchText(flight).includes(departure)) {
      return false;
    }

    if (arrival && !flightArrivalSearchText(flight).includes(arrival)) {
      return false;
    }

    if (airplane && !flightMatchesAirplaneFilter(flight, airplane)) {
      return false;
    }

    if (scheduled && String(flight.service_type || "").toUpperCase() !== scheduled) {
      return false;
    }

    return true;
  });
}

function normalizedFilterValue(selector) {
  return String(document.querySelector(selector)?.value || "").trim().toUpperCase();
}

function flightDepartureSearchText(flight) {
  return [
    flight.origin_airport_icao_code,
    flight.origin_airport_iata_code,
    flight.origin_airport_name,
    flight.origin_city,
    flight.origin_location_name
  ].map(value => String(value || "").toUpperCase()).join(" ");
}

function flightArrivalSearchText(flight) {
  return [
    flight.destination_airport_icao_code,
    flight.destination_airport_iata_code,
    flight.destination_airport_name,
    flight.destination_city,
    flight.destination_location_name
  ].map(value => String(value || "").toUpperCase()).join(" ");
}

function flightMatchesAirplaneFilter(flight, filterValue) {
  const icaoCodes = flightAirplaneIcaoCodes(flight);

  /*
   * Airplane filter is intentionally ICAO-only.
   *
   * Examples:
   * - A or A3 or A320 => matches A320
   * - C or CONC => matches CONC
   * - manufacturer/model names are ignored
   */
  return icaoCodes.some(code => code.startsWith(filterValue));
}

function flightAirplaneSearchText(flight) {
  return flightAirplaneIcaoCodes(flight).join(" ");
}

function flightAirplaneIcaoCodes(flight) {
  return [
    flight.compatible_aircraft_icao_codes,
    flight.icao_type_code
  ]
    .flatMap(splitSearchTokens)
    .filter(Boolean);
}

function renderFlights(rows) {
  updateFlightFilterSummary(rows.length);
  const tbody = document.querySelector("#routesTableBody");

  if (!rows.length) {
    tbody.innerHTML = `<tr><td colspan="5">${flightFiltersApplied ? "No flights match the current filters." : "Use the filters above to show flights."}</td></tr>`;
    return;
  }

  tbody.innerHTML = rows.map(flight => `
    <tr>
      <td>
        <strong>${escapeHtml(publicFlightCode(flight))}</strong>
      </td>
      <td>${escapeHtml(flight.origin_airport_icao_code)} → ${escapeHtml(flight.destination_airport_icao_code)}</td>
      <td>${flightScheduleLabel(flight)}</td>
      <td>${airplanesLinks(flight)}</td>
      <td>
        <div class="button-row">
          <button type="button" data-flight-detail="${flight.service_id}">Details</button>
          ${isOnDemandFlight(flight) ? `<button type="button" data-start-flight="${flight.service_id}" class="secondary">Start flight now</button>` : ""}
        </div>
      </td>
    </tr>
  `).join("");

  tbody.querySelectorAll("[data-flight-detail]").forEach(button => {
    button.addEventListener("click", () => openFlightDetail(Number(button.dataset.flightDetail)));
  });

  tbody.querySelectorAll("[data-start-flight]").forEach(button => {
    button.addEventListener("click", () => startFlightNow(Number(button.dataset.startFlight)));
  });

  tbody.querySelectorAll("[data-airplane-icao]").forEach(button => {
    button.addEventListener("click", () => openAircraftModelDialog(button.dataset.airplaneIcao));
  });
}

function openAddFlightDialog() {
  const dialog = document.querySelector("#routeDialog");

  if (!dialog) {
    showError("Flight dialog not found.");
    return;
  }

  clearDialogError();

  document.querySelector("#originAirport").value = "";
  document.querySelector("#destinationAirport").value = "";

  const typeSelect = getFlightTypeSelect();
  if (typeSelect) {
    typeSelect.value = "ON_DEMAND";
  }

  const categorySelect = document.querySelector("#routeCategory");
  if (categorySelect) {
    categorySelect.value = "";
  }

  const scheduledTime = document.querySelector("#scheduledTime");
  if (scheduledTime) {
    scheduledTime.value = "";
  }

  document.querySelector("#ticketPrice").value = "0.00";
  document.querySelector("#routePreviewPanel").hidden = true;
  document.querySelector("#routePreviewContent").innerHTML = "";

  setupFlightTypeToggle();
  setupFlightTypeExplanation();
  applyFlightTypeState();
  loadOwnedAircraftModelsForFlight();

  dialog.showModal();
}

async function previewFlight(options = {}) {
  const payload = flightFormPayload();
  const silent = Boolean(options.silent);
  const error = document.querySelector("#routeDialogError");
  const panel = document.querySelector("#routePreviewPanel");
  const content = document.querySelector("#routePreviewContent");

  error.hidden = true;
  error.textContent = "";

  if (!silent) {
    panel.hidden = false;
    content.textContent = "Calculating preview...";
  }

  try {
    const preview = await postJson(API.preview, payload);
    lastSuggestedTicketPrice = Number(preview.suggested_ticket_price || 0);

    if (Number(payload.ticket_price || 0) <= 0 && lastSuggestedTicketPrice > 0) {
      document.querySelector("#ticketPrice").value = lastSuggestedTicketPrice.toFixed(2);
    }

    if (!silent) {
      panel.hidden = false;
      content.innerHTML = renderPreview(preview);
    }
  } catch (error) {
    if (!silent) {
      panel.hidden = true;
      showDialogError(error.message || "Unable to preview flight.");
    }
  }
}

async function saveFlight(event) {
  event?.preventDefault?.();

  clearDialogError();

  try {
    await postJson(API.create, flightFormPayload());
    document.querySelector("#routeDialog").close();
    await loadFlights();
  } catch (error) {
    showDialogError(error.message || "Unable to create flight.");
  }
}

async function startFlightNow(serviceId) {
  hideError();

  try {
    const data = await getJson(API.availableAircraft(serviceId));
    const available = data.available_aircraft || [];

    if (!available.length) {
      alert("This flight cannot depart: no compatible available aircraft is present at the origin airport.");
      return;
    }

    let aircraftId = null;

    if (available.length === 1) {
      aircraftId = Number(available[0].company_aircraft_id || available[0].aircraft_id);
    } else {
      aircraftId = await chooseAircraftForOnDemandFlight(data.flight, available);
    }

    if (!aircraftId) {
      return;
    }

    const result = await postJson(API.startServiceFlight, {
      service_id: serviceId,
      company_aircraft_id: aircraftId
    });

    alert(
      `Flight ${result.flight_code} is now in flight.\n` +
      `Aircraft: ${result.aircraft?.registration_code || "-"}\n` +
      `Crew: ${result.crew?.pilot_1 || "-"} / ${result.crew?.pilot_2 || "-"}\n` +
      `Estimated profit: ${result.estimated_profit || "0.00"}`
    );

    await loadFlights();
  } catch (error) {
    showError(error.message || "Unable to start flight.");
  }
}

async function openFlightDetail(serviceId) {
  const dialog = document.querySelector("#routeDetailDialog");
  const title = document.querySelector("#routeDetailTitle");
  const content = document.querySelector("#routeDetailContent");

  title.textContent = "Flight";
  content.textContent = "Loading...";
  dialog.showModal();

  try {
    const data = await getJson(API.detail(serviceId));
    const flight = data.service;
    const instances = data.recent_flights || [];

    title.textContent = publicFlightCode(flight);

    content.innerHTML = `
      <div class="detail-grid">
        ${section("Flight", [
          ["Flight code", publicFlightCode(flight)],
          ["Type", flight.service_type || "-"],
          ["Scheduled", flightScheduleLabel(flight)],
          ["Route", `${flight.origin_airport_icao_code} → ${flight.destination_airport_icao_code}`],
          ["Origin", `${flight.origin_airport_name || "-"} (${flight.origin_airport_icao_code})`],
          ["Destination", `${flight.destination_airport_name || "-"} (${flight.destination_airport_icao_code})`],
          ["Distance", `${flight.planned_distance_km} km`],
          ["Estimated block", `${flight.estimated_block_minutes} min`],
          ["Base ticket", `${money(flight.base_ticket_price)} ${flight.currency_code}`]
        ])}
        ${section("Airplanes", [
          ["Compatible ICAO types", flight.compatible_aircraft_icao_codes || flight.icao_type_code || "-"],
          ["Internal model list", flight.compatible_aircraft_model_codes || "-"],
          ["Preferred model", `${flight.manufacturer || "-"} ${flight.model_name || ""}`]
        ])}
        ${section("Dispatch policy", [
          ["Aircraft binding", "No permanent aircraft binding at flight definition level"],
          ["Dispatch", "A real flight instance chooses a compatible aircraft at the origin airport"],
          ["Backup allowed", Number(flight.allow_backup_aircraft) ? "Yes" : "No"],
          ["Extra flights allowed", Number(flight.allow_extra_flights) ? "Yes" : "No"],
          ["Internal code", flight.service_code || "-"]
        ])}
        <section class="detail-section">
          <h3>Recent flight instances</h3>
          ${
            instances.length
              ? `<dl class="detail-list">${instances.map(instance => `
                  ${detailRow(instance.flight_code || `Flight #${instance.id}`, `${instance.flight_operation_type || "-"} · ${instance.status} · dispatch ${instance.dispatch_status || "-"} · profit ${money(instance.profit_amount)} ${instance.currency_code || ""}`)}
                `).join("")}</dl>`
              : `<p class="muted">No real flight instances generated yet.</p>`
          }
        </section>
      </div>
      <div class="dialog-action-bar">
        <button type="button" class="danger" id="removeServiceButton">Remove flight</button>
      </div>
    `;

    content.querySelector("#removeServiceButton")?.addEventListener("click", () => removeFlight(Number(flight.id || flight.service_id)));
  } catch (error) {
    content.innerHTML = `<div class="page-error">${escapeHtml(error.message || "Unable to load flight detail.")}</div>`;
  }
}

async function removeFlight(serviceId) {
  if (!confirm("Remove this flight? Existing completed flight history will remain, but this flight definition will be cancelled.")) {
    return;
  }

  try {
    await postJson(API.removeService, { service_id: serviceId });
    document.querySelector("#routeDetailDialog")?.close();
    await loadFlights();
  } catch (error) {
    alert(error.message || "Unable to remove flight.");
  }
}

async function openAircraftModelDialog(icaoCode) {
  const dialog = document.querySelector("#aircraftModelDialog") || ensureAircraftModelDialog();
  const title = dialog.querySelector("#aircraftModelTitle");
  const content = dialog.querySelector("#aircraftModelContent");

  title.textContent = `Aircraft ${icaoCode}`;
  content.textContent = "Loading...";
  dialog.showModal();

  try {
    const data = await getJson(API.aircraftByIcao(icaoCode));
    const model = data.model;

    title.textContent = `${model.icao_type_code} · ${model.manufacturer} ${model.model_name}`;
    content.innerHTML = `
      <div class="model-image-wrap">
        ${model.image_asset_path ? `<img src="${escapeHtml(model.image_asset_path)}" alt="${escapeHtml(model.manufacturer)} ${escapeHtml(model.model_name)}">` : `<p class="muted">No image available.</p>`}
      </div>
      <div class="detail-grid">
        ${section("Identity", [
          ["ICAO type", model.icao_type_code],
          ["Manufacturer", model.manufacturer],
          ["Model", model.model_name],
          ["Internal model code", model.model_code],
          ["Operation role", model.operation_role]
        ])}
        ${section("Performance", [
          ["Passengers", model.passenger_capacity_standard],
          ["Range", `${model.range_km ?? "-"} km`],
          ["Cruise speed", `${model.cruise_speed_kmh ?? "-"} km/h`],
          ["Fuel burn", `${model.fuel_burn_kg_per_hour ?? "-"} kg/h`],
          ["Maintenance cost/h", money(model.maintenance_cost_per_hour || 0)]
        ])}
        ${section("Economics", [
          ["Indicative new price", money(model.new_purchase_price || 0)]
        ])}
      </div>
    `;
  } catch (error) {
    content.innerHTML = `<div class="page-error">${escapeHtml(error.message || "Unable to load aircraft model.")}</div>`;
  }
}

function ensureAircraftModelDialog() {
  const dialog = document.createElement("dialog");
  dialog.id = "aircraftModelDialog";
  dialog.innerHTML = `
    <form method="dialog" class="dialog-card">
      <header class="dialog-header">
        <div>
          <p class="eyebrow">Generic airplane model</p>
          <h2 id="aircraftModelTitle">Aircraft</h2>
        </div>
        <button type="button" value="close" class="close-button" aria-label="Close">×</button>
      </header>
      <div id="aircraftModelContent" class="dialog-body">Loading...</div>
      <footer class="dialog-footer">
        <button value="close">Close</button>
      </footer>
    </form>
  `;

  document.body.appendChild(dialog);
  setupDialogCloseButtons();

  return dialog;
}

function renderPreview(preview) {
  return `
    <div class="detail-grid">
      ${section("Flight", [
        ["Route", `${preview.origin_airport_icao_code} → ${preview.destination_airport_icao_code}`],
        ["Distance", `${preview.planned_distance_km} km`],
        ["Duration", `${preview.planned_duration_minutes} min`],
        ["Ticket", `${money(preview.ticket_price)} ${preview.currency_code}`],
        ["Suggested ticket", `${money(preview.suggested_ticket_price || 0)} ${preview.currency_code}`]
      ])}
      ${section("Expected economics", [
        ["Expected pax", `${preview.estimates.expected.passengers} / ${preview.passenger_capacity}`],
        ["Revenue", `${money(preview.estimates.expected.revenue)} ${preview.currency_code}`],
        ["Fuel cost", `${money(preview.costs.fuel_cost)} ${preview.currency_code}`],
        ["Maintenance reserve", `${money(preview.costs.maintenance_cost)} ${preview.currency_code}`],
        ["Crew estimate", `${money(preview.costs.staff_cost)} ${preview.currency_code}`],
        ["Expected profit", `${money(preview.estimates.expected.profit)} ${preview.currency_code}`]
      ])}
    </div>
  `;
}


async function loadOwnedAircraftModelsForFlight() {
  const container = document.querySelector("#ownedAircraftModelChoices");

  if (!container) {
    return;
  }

  container.innerHTML = `<p class="muted">Loading owned airplanes...</p>`;

  try {
    const data = await getJson(API.ownedAircraftModels);
    const models = data.models || [];

    if (!models.length) {
      container.innerHTML = `<p class="muted">No owned airplanes yet. Buy an aircraft from Fleet first.</p>`;
      return;
    }

    container.innerHTML = models.map(model => `
      <label class="choice-row">
        <input
          type="checkbox"
          name="selected_aircraft_model_codes"
          value="${escapeHtml(model.model_code)}"
          ${models.length === 1 ? "checked" : ""}
        >
        <span>
          <strong>${escapeHtml(model.icao_type_code || model.model_code)}</strong>
          ${escapeHtml(model.manufacturer || "")} ${escapeHtml(model.model_name || "")}
          <small class="muted">
            Owned: ${escapeHtml(model.owned_count || 0)}
            · Available: ${escapeHtml(model.available_count || 0)}
            · Registrations: ${escapeHtml(model.registrations || "-")}
          </small>
        </span>
      </label>
    `).join("");
  } catch (error) {
    container.innerHTML = `<p class="page-error">${escapeHtml(error.message || "Unable to load owned airplanes.")}</p>`;
  }
}

function selectedAircraftModelCodes() {
  return Array.from(document.querySelectorAll("input[name='selected_aircraft_model_codes']:checked"))
    .map(input => input.value)
    .filter(Boolean);
}


function flightFormPayload() {
  const type = getFlightTypeSelect()?.value || "ON_DEMAND";
  const scheduledTime = type === "SCHEDULED"
    ? (document.querySelector("#scheduledTime")?.value || "10:00")
    : "";

  return {
    service_type: type,
    flight_type: type,
    route_category_code: document.querySelector("#routeCategory")?.value || "",
    selected_aircraft_model_codes: selectedAircraftModelCodes(),
    origin_airport_icao_code: document.querySelector("#originAirport").value.trim().toUpperCase(),
    destination_airport_icao_code: document.querySelector("#destinationAirport").value.trim().toUpperCase(),
    scheduled_departure_time_utc: scheduledTime,
    ticket_price: Number(document.querySelector("#ticketPrice").value)
  };
}

function routeFormPayload() {
  return flightFormPayload();
}

function getFlightTypeSelect() {
  return document.querySelector("#serviceType") || document.querySelector("#flightType");
}

function setupFlightTypeToggle() {
  const typeSelect = getFlightTypeSelect();
  const scheduledTime = document.querySelector("#scheduledTime");

  if (!typeSelect || !scheduledTime) {
    return;
  }

  const refresh = () => applyFlightTypeState();

  if (!typeSelect.dataset.bound) {
    typeSelect.dataset.bound = "true";
    typeSelect.addEventListener("change", refresh);
    typeSelect.addEventListener("input", refresh);
  }

  refresh();
}

function applyFlightTypeState() {
  const typeSelect = getFlightTypeSelect();
  const scheduledTime = document.querySelector("#scheduledTime");

  if (!typeSelect || !scheduledTime) {
    return;
  }

  if (typeSelect.value === "SCHEDULED") {
    scheduledTime.disabled = false;
    scheduledTime.required = true;
    scheduledTime.removeAttribute("disabled");
    scheduledTime.removeAttribute("aria-disabled");

    if (!scheduledTime.value) {
      scheduledTime.value = "10:00";
    }
  } else {
    scheduledTime.value = "";
    scheduledTime.required = false;
    scheduledTime.disabled = true;
    scheduledTime.setAttribute("disabled", "disabled");
    scheduledTime.setAttribute("aria-disabled", "true");
  }
}

function setupFlightTypeExplanation() {
  const typeSelect = getFlightTypeSelect();
  const explanation = document.querySelector("#flightTypeExplanation");

  if (!typeSelect || !explanation) {
    return;
  }

  const refresh = () => {
    if (typeSelect.value === "SCHEDULED") {
      explanation.textContent = "Scheduled flight: recurring planned flight with a fixed UTC departure time. The aircraft must be available at the origin airport when departure time arrives.";
    } else {
      explanation.textContent = "On-demand flight: manual non-scheduled flight that can be started when compatible aircraft and crew are available. Useful for extra income, but it may interfere with later scheduled flights.";
    }
  };

  if (!typeSelect.dataset.explanationBound) {
    typeSelect.dataset.explanationBound = "true";
    typeSelect.addEventListener("change", refresh);
    typeSelect.addEventListener("input", refresh);
  }

  refresh();
}

function setupTicketSuggestion() {
  const origin = document.querySelector("#originAirport");
  const destination = document.querySelector("#destinationAirport");
  const ticket = document.querySelector("#ticketPrice");

  if (!origin || !destination || !ticket || ticket.dataset.suggestionBound) {
    return;
  }

  ticket.dataset.suggestionBound = "true";

  const maybeSuggest = debounce(async () => {
    const originValue = origin.value.trim().toUpperCase();
    const destinationValue = destination.value.trim().toUpperCase();

    if (originValue.length !== 4 || destinationValue.length !== 4 || originValue === destinationValue) {
      return;
    }

    if (Number(ticket.value || 0) > 0) {
      return;
    }

    await previewFlight({ silent: true });
  }, 450);

  origin.addEventListener("input", maybeSuggest);
  destination.addEventListener("input", maybeSuggest);
  origin.addEventListener("blur", maybeSuggest);
  destination.addEventListener("blur", maybeSuggest);
}

function setupDialogCloseButtons() {
  document.querySelectorAll("dialog .close-button, dialog [data-dialog-close]").forEach(button => {
    if (button.dataset.closeBound) {
      return;
    }

    button.dataset.closeBound = "true";
    button.setAttribute("type", "button");

    button.addEventListener("click", event => {
      event.preventDefault();
      button.closest("dialog")?.close();
    });
  });
}

function clearDialogError() {
  const error = document.querySelector("#routeDialogError");
  if (error) {
    error.hidden = true;
    error.textContent = "";
  }
}

function showDialogError(message) {
  const error = document.querySelector("#routeDialogError");
  if (error) {
    error.hidden = false;
    error.textContent = message;
  }
}

function isOnDemandFlight(flight) {
  const type = flight.service_type || (flight.scheduled_departure_time_utc ? "SCHEDULED" : "ON_DEMAND");
  return type === "ON_DEMAND";
}

function flightScheduleLabel(flight) {
  const type = flight.service_type || (flight.scheduled_departure_time_utc ? "SCHEDULED" : "ON_DEMAND");

  if (type === "ON_DEMAND") {
    return "Not scheduled";
  }

  const raw = flight.scheduled_departure_time_utc || "";
  return raw.length >= 5 ? raw.slice(0, 5) : "-";
}

function publicFlightCode(row) {
  const explicitCode = row.flight_route_code || row.public_flight_code;

  if (explicitCode && !String(explicitCode).match(/^[A-Z]{3}-[0-9]{4}-/)) {
    return explicitCode;
  }

  const internal = String(row.service_code || "");
  const match = internal.match(/^([A-Z]{3}-[0-9]{4})-/);

  if (match) {
    return match[1];
  }

  return internal || row.route_code || "-";
}

function airplanesLinks(flight) {
  const raw = flight.compatible_aircraft_icao_codes || flight.icao_type_code || "C208";
  const codes = String(raw)
    .split(",")
    .map(code => code.trim())
    .filter(Boolean);

  return codes.map(code => `
    <button type="button" class="link-button airplane-code-link" data-airplane-icao="${escapeHtml(code)}">${escapeHtml(code)}</button>
  `).join(" ");
}

function section(title, rows) {
  return `<section class="detail-section"><h3>${escapeHtml(title)}</h3><dl class="detail-list">${rows.map(([key, value]) => detailRow(key, value)).join("")}</dl></section>`;
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

async function postJson(url, payload) {
  const response = await fetch(url, {
    method: "POST",
    headers: {
      "Accept": "application/json",
      "Content-Type": "application/json"
    },
    credentials: "same-origin",
    body: JSON.stringify(payload)
  });

  const body = await response.json().catch(() => null);

  if (!response.ok) {
    throw new Error(body?.message || body?.error || `Request failed: ${response.status}`);
  }

  return body;
}

function summaryRow(label, value) {
  return `<div><dt>${escapeHtml(label)}</dt><dd>${escapeHtml(value ?? "-")}</dd></div>`;
}

function detailRow(label, value) {
  return `<div><dt>${escapeHtml(label)}</dt><dd>${escapeHtml(value ?? "-")}</dd></div>`;
}

function startUtcClock() {
  const clock = document.querySelector("#utcClock");

  if (!clock) {
    return;
  }

  const tick = () => {
    clock.textContent = `${new Date().toISOString().replace("T", " ").slice(0, 19)} UTC`;
  };

  tick();
  window.setInterval(tick, 1000);
}

function money(value) {
  return Number(value || 0).toLocaleString("en-US", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  });
}

function debounce(callback, waitMs) {
  let timeoutId = null;

  return (...args) => {
    window.clearTimeout(timeoutId);
    timeoutId = window.setTimeout(() => callback(...args), waitMs);
  };
}

function showError(message) {
  const error = document.querySelector("#pageError");
  if (error) {
    error.hidden = false;
    error.textContent = message;
  }
}

function hideError() {
  const error = document.querySelector("#pageError");
  if (error) {
    error.hidden = true;
    error.textContent = "";
  }
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}


function chooseAircraftForOnDemandFlight(flight, aircraft) {
  return new Promise(resolve => {
    const dialog = document.createElement("dialog");
    dialog.id = "chooseAircraftDialog";
    dialog.innerHTML = `
      <form method="dialog" class="dialog-card">
        <header class="dialog-header">
          <div>
            <p class="eyebrow">Manual dispatch</p>
            <h2>Choose aircraft</h2>
          </div>
          <button type="button" class="close-button" aria-label="Close">×</button>
        </header>
        <div class="dialog-body">
          <p class="muted">
            Non-scheduled flights require manual aircraft selection.
            Only compatible available aircraft at ${escapeHtml(flight.origin_airport_icao_code)} are listed.
          </p>
          <div class="aircraft-choice-list">
            ${aircraft.map((a, index) => `
              <label class="aircraft-choice-row">
                <input type="radio" name="dispatch_aircraft" value="${escapeHtml(a.company_aircraft_id || a.aircraft_id)}" ${index === 0 ? "checked" : ""}>
                <span>
                  <strong>${escapeHtml(a.registration_code)} · ${escapeHtml(a.icao_type_code || a.model_code)}</strong>
                  ${escapeHtml(a.manufacturer || "")} ${escapeHtml(a.model_name || "")}
                  <small class="muted">
                    Condition ${escapeHtml(a.condition_percent ?? "-")}%
                    · Estimated score ${money(a.estimated_profit_score || 0)}
                  </small>
                </span>
              </label>
            `).join("")}
          </div>
        </div>
        <footer class="dialog-footer">
          <button type="button" id="cancelAircraftChoice">Cancel</button>
          <button type="button" id="confirmAircraftChoice" class="primary">Start flight</button>
        </footer>
      </form>
    `;
    document.body.appendChild(dialog);
    const close = value => {
      dialog.close();
      dialog.remove();
      resolve(value);
    };
    dialog.querySelector(".close-button").addEventListener("click", () => close(null));
    dialog.querySelector("#cancelAircraftChoice").addEventListener("click", () => close(null));
    dialog.querySelector("#confirmAircraftChoice").addEventListener("click", () => {
      const selected = dialog.querySelector("input[name='dispatch_aircraft']:checked");
      close(selected ? Number(selected.value) : null);
    });
    dialog.showModal();
  });
}


function splitSearchTokens(value) {
  return String(value || "")
    .toUpperCase()
    .split(/[^A-Z0-9]+/)
    .map(token => token.trim())
    .filter(Boolean);
}
