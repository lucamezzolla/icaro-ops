const API = {
  routes: "api/public/routes/list.php",
  create: "api/public/routes/create.php",
  update: "api/public/routes/update.php",
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
let editingFlightServiceId = null;

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
          <button type="button" data-edit-flight="${flight.service_id}" class="secondary">Edit</button>
          ${isOnDemandFlight(flight) ? `<button type="button" data-start-flight="${flight.service_id}" class="secondary">Start flight now</button>` : ""}
        </div>
      </td>
    </tr>
  `).join("");

  tbody.querySelectorAll("[data-flight-detail]").forEach(button => {
    button.addEventListener("click", () => openFlightDetail(Number(button.dataset.flightDetail)));
  });

  tbody.querySelectorAll("[data-edit-flight]").forEach(button => {
    button.addEventListener("click", () => openEditFlightDialog(Number(button.dataset.editFlight)));
  });

  tbody.querySelectorAll("[data-start-flight]").forEach(button => {
    button.addEventListener("click", () => startFlightNow(Number(button.dataset.startFlight)));
  });

  tbody.querySelectorAll("[data-airplane-icao]").forEach(button => {
    button.addEventListener("click", () => openAircraftModelDialog(button.dataset.airplaneIcao));
  });
}

function resetFlightEconomicsPreview() {
  const previewPanel = document.querySelector("#routePreviewPanel");
  const previewContent = document.querySelector("#routePreviewContent");

  if (previewPanel) {
    previewPanel.hidden = true;
  }

  if (previewContent) {
    previewContent.innerHTML = "";
  }

  const economicPreviewContent = document.querySelector("#economicPreviewContent");
  if (economicPreviewContent) {
    economicPreviewContent.textContent = "Select a route and airplane, then click Preview economics.";
  }
}

function openAddFlightDialog() {
  editingFlightServiceId = null;

  const dialog = document.querySelector("#routeDialog");

  if (!dialog) {
    showError("Flight dialog not found.");
    return;
  }

  clearDialogError();

  document.querySelector("#routeDialogTitle").textContent = "Add flight";
  document.querySelector("#saveRouteButton").textContent = "Create flight";
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
  const economicPreviewContent = document.querySelector("#economicPreviewContent");
  if (economicPreviewContent) {
    economicPreviewContent.textContent = "Select a route and airplane, then click Preview economics.";
  }

  setupFlightTypeToggle();
  setupFlightTypeExplanation();
  applyFlightTypeState();
  loadOwnedAircraftModelsForFlight();

  dialog.showModal();
}

async function openEditFlightDialog(serviceId) {
  hideError();
  clearDialogError();

  const dialog = document.querySelector("#routeDialog");

  if (!dialog) {
    showError("Flight dialog not found.");
    return;
  }

  try {
    const data = await getJson(API.detail(serviceId));
    const flight = data.service;

    editingFlightServiceId = Number(flight.id || flight.service_id || serviceId);

    document.querySelector("#routeDialogTitle").textContent = `Edit flight ${publicFlightCode(flight)}`;
    document.querySelector("#saveRouteButton").textContent = "Save changes";
    document.querySelector("#originAirport").value = flight.origin_airport_icao_code || "";
    document.querySelector("#destinationAirport").value = flight.destination_airport_icao_code || "";

    const typeSelect = getFlightTypeSelect();
    if (typeSelect) {
      typeSelect.value = flight.service_type || (flight.scheduled_departure_time_utc ? "SCHEDULED" : "ON_DEMAND");
    }

    const categorySelect = document.querySelector("#routeCategory");
    if (categorySelect) {
      categorySelect.value = flight.route_category_code || "";
    }

    const scheduledTime = document.querySelector("#scheduledTime");
    if (scheduledTime) {
      scheduledTime.value = String(flight.scheduled_departure_time_utc || "").slice(0, 5);
    }

    document.querySelector("#ticketPrice").value = Number(flight.base_ticket_price || flight.ticket_price || 0).toFixed(2);
    resetFlightEconomicsPreview();

    setupFlightTypeToggle();
    setupFlightTypeExplanation();
    applyFlightTypeState();
    await loadOwnedAircraftModelsForFlight(splitModelCodes(flight.compatible_aircraft_model_codes));

    dialog.showModal();
  } catch (error) {
    showError(error.message || "Unable to load flight for editing.");
  }
}

async function previewFlight(options = {}) {
  const payload = flightFormPayload();
  const silent = Boolean(options.silent);
  const error = document.querySelector("#routeDialogError");
  const dialog = document.querySelector("#economicPreviewDialog");
  const content = document.querySelector("#economicPreviewContent");

  if (error) {
    error.hidden = true;
    error.textContent = "";
  }

  if (!silent) {
    if (!dialog || !content) {
      showDialogError("Economic preview dialog not found.");
      return;
    }

    content.innerHTML = `<p class="muted">Calculating route economics...</p>`;
    dialog.showModal();
  }

  try {
    const preview = await postJson(API.preview, payload);
    lastSuggestedTicketPrice = Number(preview.suggested_ticket_price || 0);

    if (Number(payload.ticket_price || 0) <= 0 && lastSuggestedTicketPrice > 0) {
      document.querySelector("#ticketPrice").value = lastSuggestedTicketPrice.toFixed(2);
    }

    if (!silent && content) {
      content.innerHTML = renderPreview(preview);
    }
  } catch (error) {
    if (!silent && content) {
      content.innerHTML = `<p class="page-error">${escapeHtml(error.message || "Unable to preview flight economics.")}</p>`;
    } else if (!silent) {
      showDialogError(error.message || "Unable to preview flight economics.");
    }
  }
}

async function saveFlight(event) {
  event?.preventDefault?.();

  clearDialogError();

  const payload = flightFormPayload();
  const isEditing = Boolean(editingFlightServiceId);

  if (isEditing) {
    payload.service_id = editingFlightServiceId;
  }

  try {
    await postJson(isEditing ? API.update : API.create, payload);
    document.querySelector("#routeDialog").close();
    editingFlightServiceId = null;
    await loadFlights();
  } catch (error) {
    showDialogError(error.message || (isEditing ? "Unable to update flight." : "Unable to create flight."));
  }
}

async function startFlightNow(serviceId) {
  hideError();

  try {
    const data = await getJson(API.availableAircraft(serviceId));
    const available = data.available_aircraft || [];

    if (!available.length) {
      showError("This flight cannot depart: no compatible available aircraft is present at the origin airport.");
      return;
    }

    const aircraftId = await chooseAircraftForOnDemandFlight(data.flight, available);

    if (!aircraftId) {
      return;
    }

    const result = await postJson(API.startServiceFlight, {
      service_id: serviceId,
      company_aircraft_id: aircraftId
    });

    await showStartedFlightDialog(result);
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
        <button type="button" id="editServiceButton" class="secondary">Edit flight</button>
        <button type="button" class="danger" id="removeServiceButton">Remove flight</button>
      </div>
    `;

    content.querySelector("#editServiceButton")?.addEventListener("click", () => {
      document.querySelector("#routeDetailDialog")?.close();
      openEditFlightDialog(Number(flight.id || flight.service_id));
    });

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
  const currency = preview.currency_code || "EUR";
  const scenarios = preview.load_factor_scenarios || [];
  const aircraftPreviews = preview.aircraft_previews || [];
  const aircraft = preview.aircraft || {};

  return `
    <div class="economic-preview-grid">
      <section class="detail-section economic-preview-hero">
        <h3>${escapeHtml(preview.origin_airport_icao_code)} → ${escapeHtml(preview.destination_airport_icao_code)}</h3>
        <p class="muted">
          Forecast based on ${escapeHtml(previewAircraftLabel(aircraft))}.
          If multiple aircraft are selected, Icaro Ops prices the flight using the most expensive compatible aircraft.
        </p>
        <div class="economic-preview-kpis">
          ${previewKpi("Distance", `${money(preview.planned_distance_km)} km`)}
          ${previewKpi("Duration", `${escapeHtml(preview.planned_duration_minutes)} min`)}
          ${previewKpi("Capacity", `${escapeHtml(preview.passenger_capacity)} pax`)}
          ${previewKpi("Ticket", formatPreviewMoney(preview.ticket_price, currency))}
          ${previewKpi("Suggested", formatPreviewMoney(preview.suggested_ticket_price, currency))}
          ${previewKpi("Break-even pax", preview.break_even_passengers ?? "-")}
        </div>
        <p class="economic-preview-recommendation">${escapeHtml(preview.recommendation || "")}</p>
      </section>

      ${section("Flight operating costs", [
        ["Fuel", formatPreviewMoney(preview.costs?.fuel_cost, currency)],
        ["Maintenance reserve", formatPreviewMoney(preview.costs?.maintenance_cost, currency)],
        ["Crew", formatPreviewMoney(preview.costs?.staff_cost, currency)],
        ["Total operating cost", formatPreviewMoney(preview.costs?.total_operating_cost, currency)],
        ["Break-even ticket at 75%", formatPreviewMoney(preview.break_even_ticket_at_expected_load, currency)]
      ])}
    </div>

    <section class="detail-section economic-preview-section">
      <h3>Profit forecast by passenger load</h3>
      <p class="muted">Break-even is the minimum cost-covering price. Market recommended ticket rises with demand, seat scarcity and aircraft prestige.</p>
      ${renderEconomicScenarioTable(scenarios, currency)}
    </section>

    ${aircraftPreviews.length > 1 ? `
      <section class="detail-section economic-preview-section">
        <h3>Selected aircraft comparison</h3>
        <p class="muted">The suggested ticket protects the most expensive selected aircraft, so cheaper aircraft should have better margins.</p>
        ${renderAircraftPreviewTable(aircraftPreviews, currency)}
      </section>
    ` : ""}

    <section class="detail-section economic-preview-section">
      <h3>Cost model notes</h3>
      <ul class="economic-preview-notes">
        <li>${escapeHtml(preview.cost_model?.fuel_note || "Fuel cost is estimated from aircraft fuel burn and block time.")}</li>
        <li>${escapeHtml(preview.cost_model?.maintenance_note || "Maintenance reserve is charged per estimated flight hour.")}</li>
        <li>${escapeHtml(preview.cost_model?.fixed_cost_note || "Fixed company costs are not included in this single-flight preview.")}</li>
        <li>${escapeHtml(preview.cost_model?.market_pricing_note || "Market recommended ticket rises with demand and seat scarcity; break-even remains the minimum cost-covering price.")}</li>
        <li>Qualified pilots found: ${escapeHtml(preview.cost_model?.qualified_pilots_found ?? 0)} / ${escapeHtml(preview.cost_model?.required_pilots ?? 2)}</li>
      </ul>
    </section>
  `;
}

function renderEconomicScenarioTable(scenarios, currency) {
  if (!scenarios.length) {
    return `<p class="muted">No scenarios available.</p>`;
  }

  return `
    <div class="table-wrap economic-preview-table-wrap">
      <table class="economic-preview-table">
        <thead>
          <tr>
            <th>Load</th>
            <th>Pax</th>
            <th>Revenue</th>
            <th>Fuel</th>
            <th>Maintenance</th>
            <th>Crew</th>
            <th>Total cost</th>
            <th>Profit</th>
            <th>Break-even ticket</th>
            <th>Market ticket</th>
            <th>Market profit</th>
            <th>Signal</th>
          </tr>
        </thead>
        <tbody>
          ${scenarios.map(row => `
            <tr>
              <td>${escapeHtml(row.load_factor_percent)}%</td>
              <td>${escapeHtml(row.passengers)}</td>
              <td>${formatPreviewMoney(row.revenue, currency)}</td>
              <td>${formatPreviewMoney(row.fuel_cost, currency)}</td>
              <td>${formatPreviewMoney(row.maintenance_cost, currency)}</td>
              <td>${formatPreviewMoney(row.staff_cost, currency)}</td>
              <td>${formatPreviewMoney(row.total_operating_cost, currency)}</td>
              <td class="${previewProfitClass(row.profit)}">${formatPreviewMoney(row.profit, currency)}</td>
              <td>${formatPreviewMoney(row.break_even_ticket_price, currency)}</td>
              <td>${formatPreviewMoney(row.market_recommended_ticket_price, currency)}</td>
              <td class="${previewProfitClass(row.market_profit)}">${formatPreviewMoney(row.market_profit, currency)}</td>
              <td>${escapeHtml(row.market_signal || "-")}</td>
            </tr>
          `).join("")}
        </tbody>
      </table>
    </div>
  `;
}

function renderAircraftPreviewTable(rows, currency) {
  return `
    <div class="table-wrap economic-preview-table-wrap">
      <table class="economic-preview-table">
        <thead>
          <tr>
            <th>Aircraft</th>
            <th>Capacity</th>
            <th>Duration</th>
            <th>Total cost</th>
            <th>75% pax</th>
            <th>75% profit</th>
            <th>Break-even ticket</th>
          </tr>
        </thead>
        <tbody>
          ${rows.map(row => `
            <tr>
              <td>${escapeHtml(previewAircraftLabel(row.aircraft || {}))}</td>
              <td>${escapeHtml(row.passenger_capacity)}</td>
              <td>${escapeHtml(row.planned_duration_minutes)} min</td>
              <td>${formatPreviewMoney(row.costs?.total_operating_cost, currency)}</td>
              <td>${escapeHtml(row.expected_passengers)}</td>
              <td class="${previewProfitClass(row.expected_profit)}">${formatPreviewMoney(row.expected_profit, currency)}</td>
              <td>${formatPreviewMoney(row.break_even_ticket_at_expected_load, currency)}</td>
            </tr>
          `).join("")}
        </tbody>
      </table>
    </div>
  `;
}

function previewKpi(label, value) {
  return `<div><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong></div>`;
}

function previewAircraftLabel(aircraft) {
  return [aircraft.icao_type_code || aircraft.model_code, aircraft.manufacturer, aircraft.model_name]
    .filter(Boolean)
    .join(" · ");
}

function formatPreviewMoney(value, currencyCode) {
  const amount = Number(value || 0).toLocaleString("en-US", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  });

  if (currencyCode === "EUR") {
    return `€ ${amount}`;
  }

  if (currencyCode === "USD") {
    return `$ ${amount}`;
  }

  return `${amount} ${currencyCode || ""}`.trim();
}

function previewProfitClass(value) {
  return Number(value || 0) >= 0 ? "profit-positive" : "profit-negative";
}


async function loadOwnedAircraftModelsForFlight(selectedModelCodes = []) {
  const container = document.querySelector("#ownedAircraftModelChoices");

  if (!container) {
    return;
  }

  const selected = new Set((selectedModelCodes || []).map(code => String(code || "").trim().toUpperCase()).filter(Boolean));

  container.innerHTML = `<p class="muted">Loading owned airplanes...</p>`;

  try {
    const data = await getJson(API.ownedAircraftModels);
    const models = data.models || [];

    if (!models.length) {
      container.innerHTML = `<p class="muted">No owned airplanes yet. Buy an aircraft from Fleet first.</p>`;
      return;
    }

    container.innerHTML = models.map(model => {
      const code = String(model.model_code || "").trim().toUpperCase();
      const checked = selected.size ? selected.has(code) : models.length === 1;

      return `
        <label class="choice-row">
          <input
            type="checkbox"
            name="selected_aircraft_model_codes"
            value="${escapeHtml(model.model_code)}"
            ${checked ? "checked" : ""}
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
      `;
    }).join("");

    if (selected.size && !Array.from(container.querySelectorAll("input[name='selected_aircraft_model_codes']:checked")).length) {
      container.insertAdjacentHTML("afterbegin", `<p class="page-error">The previously selected airplane model is no longer in your fleet. Select a new model before saving.</p>`);
    }
  } catch (error) {
    container.innerHTML = `<p class="page-error">${escapeHtml(error.message || "Unable to load owned airplanes.")}</p>`;
  }
}

function splitModelCodes(value) {
  return String(value || "")
    .split(",")
    .map(code => code.trim().toUpperCase())
    .filter(Boolean);
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


function showStartedFlightDialog(result) {
  return new Promise(resolve => {
    const dialog = document.createElement("dialog");
    dialog.id = "startedFlightDialog";
    dialog.innerHTML = `
      <form method="dialog" class="dialog-card">
        <header class="dialog-header">
          <div>
            <p class="eyebrow">Flight started</p>
            <h2>${escapeHtml(result.flight_code || "Flight")}</h2>
          </div>
          <button type="button" class="close-button" aria-label="Close">×</button>
        </header>

        <div class="dialog-body">
          <section class="dispatch-summary-card">
            <h3>Dispatch summary</h3>
            <dl class="detail-list">
              ${detailRow("Status", result.status || "IN_FLIGHT")}
              ${detailRow("Flight code", result.flight_code || "-")}
              ${detailRow("Aircraft", `${result.aircraft?.registration_code || "-"} · ${result.aircraft?.icao_type_code || result.aircraft?.model_code || "-"}`)}
              ${detailRow("Crew", `${result.crew?.pilot_1 || "-"} / ${result.crew?.pilot_2 || "-"}`)}
              ${detailRow("Technician", result.crew?.technician || "-")}
              ${detailRow("Estimated profit", `${money(result.estimated_profit || 0)} ${result.currency_code || "EUR"}`)}
              ${detailRow("Scheduled arrival UTC", result.scheduled_arrival_at_utc || "-")}
            </dl>
          </section>
        </div>

        <footer class="dialog-footer">
          <button type="button" id="closeStartedFlightDialog" class="primary">Close</button>
        </footer>
      </form>
    `;

    document.body.appendChild(dialog);

    const close = () => {
      dialog.close();
      dialog.remove();
      resolve();
    };

    dialog.querySelector(".close-button").addEventListener("click", close);
    dialog.querySelector("#closeStartedFlightDialog").addEventListener("click", close);
    dialog.showModal();
  });
}

function chooseAircraftForOnDemandFlight(flight, aircraft) {
  return new Promise(resolve => {
    const dialog = document.createElement("dialog");
    dialog.id = "chooseAircraftDialog";
    const hasMultipleAircraft = aircraft.length > 1;

    dialog.innerHTML = `
      <form method="dialog" class="dialog-card">
        <header class="dialog-header">
          <div>
            <p class="eyebrow">Manual dispatch</p>
            <h2>${hasMultipleAircraft ? "Choose aircraft" : "Confirm aircraft"}</h2>
          </div>
          <button type="button" class="close-button" aria-label="Close">×</button>
        </header>

        <div class="dialog-body">
          <section class="dispatch-summary-card">
            <h3>Non-scheduled flight</h3>
            <dl class="detail-list">
              ${detailRow("Flight", flight.flight_code || "-")}
              ${detailRow("Type", flight.service_type || "ON_DEMAND")}
              ${detailRow("Route", `${flight.origin_airport_icao_code || "-"} → ${flight.destination_airport_icao_code || "-"}`)}
              ${detailRow("Configured aircraft models", flight.compatible_aircraft_model_codes || "-")}
            </dl>
            <p class="muted">
              Select the aircraft to use for this on-demand departure. The server will validate the choice again before starting the flight, because the aircraft may no longer be available or may fail another dispatch check.
            </p>
          </section>

          <section class="detail-section">
            <label class="dispatch-aircraft-select-field" for="dispatchAircraftSelect">
              <span>Aircraft at ${escapeHtml(flight.origin_airport_icao_code || "-")}</span>
              <select id="dispatchAircraftSelect">
                ${aircraft.map((a, index) => `
                  <option value="${escapeHtml(a.company_aircraft_id || a.aircraft_id)}" ${index === 0 ? "selected" : ""}>
                    ${escapeHtml(formatDispatchAircraftOption(a))}
                  </option>
                `).join("")}
              </select>
            </label>

            <div class="dispatch-selected-aircraft" id="dispatchSelectedAircraft"></div>
          </section>
        </div>

        <footer class="dialog-footer">
          <button type="button" id="cancelAircraftChoice">Cancel</button>
          <button type="button" id="confirmAircraftChoice" class="primary">Start flight</button>
        </footer>
      </form>
    `;

    document.body.appendChild(dialog);

    const select = dialog.querySelector("#dispatchAircraftSelect");
    const selectedBox = dialog.querySelector("#dispatchSelectedAircraft");

    const renderSelectedAircraft = () => {
      const selectedAircraft = aircraft.find(a => Number(a.company_aircraft_id || a.aircraft_id) === Number(select.value));
      selectedBox.innerHTML = selectedAircraft ? renderDispatchAircraftDetails(selectedAircraft) : "";
    };

    const close = value => {
      dialog.close();
      dialog.remove();
      resolve(value);
    };

    select.addEventListener("change", renderSelectedAircraft);
    dialog.querySelector(".close-button").addEventListener("click", () => close(null));
    dialog.querySelector("#cancelAircraftChoice").addEventListener("click", () => close(null));
    dialog.querySelector("#confirmAircraftChoice").addEventListener("click", () => {
      close(select.value ? Number(select.value) : null);
    });

    renderSelectedAircraft();
    dialog.showModal();
  });
}

function formatDispatchAircraftOption(aircraft) {
  const registration = aircraft.registration_code || "Unknown registration";
  const type = aircraft.icao_type_code || aircraft.model_code || "Unknown type";
  const model = [aircraft.manufacturer, aircraft.model_name].filter(Boolean).join(" ");
  const condition = aircraft.condition_percent ?? "-";

  return `${registration} · ${type}${model ? ` · ${model}` : ""} · condition ${condition}%`;
}

function renderDispatchAircraftDetails(aircraft) {
  return `
    <dl class="detail-list">
      ${detailRow("Registration", aircraft.registration_code || "-")}
      ${detailRow("Type", aircraft.icao_type_code || aircraft.model_code || "-")}
      ${detailRow("Model", `${aircraft.manufacturer || ""} ${aircraft.model_name || ""}`.trim() || "-")}
      ${detailRow("Current airport", aircraft.current_airport_icao_code || "-")}
      ${detailRow("Status", aircraft.status || "-")}
      ${detailRow("Condition", `${aircraft.condition_percent ?? "-"}%`)}
      ${detailRow("Estimated score", money(aircraft.estimated_profit_score || 0))}
    </dl>
  `;
}


function splitSearchTokens(value) {
  return String(value || "")
    .toUpperCase()
    .split(/[^A-Z0-9]+/)
    .map(token => token.trim())
    .filter(Boolean);
}
