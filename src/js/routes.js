const API = {
  routes: "api/public/routes/list.php",
  create: "api/public/routes/create.php",
  detail: id => `api/public/routes/detail.php?serviceId=${encodeURIComponent(id)}`,
  preview: "api/public/routes/preview.php",
  startServiceFlight: "api/public/flights/start-service-now.php",
  removeService: "api/public/routes/delete.php",
  aircraftByIcao: code => `api/public/fleet/model-by-icao.php?icao=${encodeURIComponent(code)}`
};

let services = [];
let lastSuggestedTicketPrice = null;

function getFlightTypeSelect() {
  return getFlightTypeSelect() || document.querySelector("#flightType");
}


document.addEventListener("DOMContentLoaded", async () => {
  startUtcClock();
  document.querySelector("#refreshButton")?.addEventListener("click", loadRoutes);
  document.querySelector("#addRouteButton")?.addEventListener("click", openAddRouteDialog);
  document.querySelector("#previewRouteButton")?.addEventListener("click", previewRoute);
  document.querySelector("#saveRouteButton")?.addEventListener("click", saveRoute);
  setupTicketSuggestion();
  setupServiceTypeToggle();
  setupFlightTypeExplanation();
  setupDialogCloseButtons();
  await loadRoutes();
});

async function loadRoutes() {
  hideError();

  try {
    services = await getJson(API.routes);
    renderSummary(services);
    renderRoutes(services);
  } catch (error) {
    showError(error.message || "Unable to load services.");
  }
}

function renderSummary(rows) {
  const active = rows.filter(r => r.status === "ACTIVE").length;
  const flights = rows.reduce((total, r) => total + Number(r.generated_flights_count || 0), 0);

  document.querySelector("#routesSummary").innerHTML = `
    ${summaryRow("Services", rows.length)}
    ${summaryRow("Active", active)}
    ${summaryRow("Flights", flights)}
  `;
}

function renderRoutes(rows) {
  const tbody = document.querySelector("#routesTableBody");

  if (!rows.length) {
    tbody.innerHTML = `<tr><td colspan="5">No flights yet.</td></tr>`;
    return;
  }

  tbody.innerHTML = rows.map(service => `
    <tr>
      <td>
        <strong>${escapeHtml(service.flight_route_code || service.service_code)}</strong>
        <div class="muted">${escapeHtml(publicFlightCode(service))}</div>
      </td>
      <td>${escapeHtml(service.origin_airport_icao_code)} → ${escapeHtml(service.destination_airport_icao_code)}</td>
      <td>${serviceScheduleLabel(service)}</td>
      <td>${airplanesLinks(service)}</td>
      <td>
        <div class="button-row">
          <button type="button" data-service-detail="${service.service_id}">Details</button>
          ${isOnDemandService(service) ? `<button type="button" data-start-service="${service.service_id}" class="secondary">Start flight now</button>` : ""}
        </div>
      </td>
    </tr>
  `).join("");

  tbody.querySelectorAll("[data-service-detail]").forEach(button => {
    button.addEventListener("click", () => openRouteDetail(Number(button.dataset.serviceDetail)));
  });

  tbody.querySelectorAll("[data-start-service]").forEach(button => {
    button.addEventListener("click", () => startServiceFlight(Number(button.dataset.startService)));
  });

  tbody.querySelectorAll("[data-airplane-icao]").forEach(button => {
    button.addEventListener("click", () => openAircraftModelDialog(button.dataset.airplaneIcao));
  });
}


async function startServiceFlight(serviceId) {
  hideError();

  if (!confirm("Create and start a real flight instance for this flight now?")) {
    return;
  }

  try {
    const result = await postJson(API.startServiceFlight, { service_id: serviceId });

    alert(
      `Flight ${result.flight_code} is now in flight.\n` +
      `Aircraft: ${result.aircraft?.registration_code || "-"}\n` +
      `Crew: ${result.crew?.pilot_1 || "-"} / ${result.crew?.pilot_2 || "-"}\n` +
      `Estimated profit: ${result.estimated_profit || "0.00"}`
    );

    await loadRoutes();
  } catch (error) {
    showError(error.message || "Unable to start service flight.");
  }
}




function isOnDemandService(service) {
  const type = service.service_type || (service.scheduled_departure_time_utc ? "SCHEDULED" : "ON_DEMAND");
  return type === "ON_DEMAND";
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

function serviceScheduleLabel(service) {
  const type = service.service_type || (service.scheduled_departure_time_utc ? "SCHEDULED" : "ON_DEMAND");

  if (type === "ON_DEMAND") {
    return "Not scheduled";
  }

  const raw = service.scheduled_departure_time_utc || "";
  return raw.length >= 5 ? raw.slice(0, 5) : "-";
}

function modelCodesLabel(service) {
  return escapeHtml(service.compatible_aircraft_icao_codes || service.icao_type_code || "C208");
}

function airplanesLinks(service) {
  const raw = service.compatible_aircraft_icao_codes || service.icao_type_code || "C208";
  const codes = String(raw).split(",").map(code => code.trim()).filter(Boolean);

  return codes.map(code => `
    <button type="button" class="link-button airplane-code-link" data-airplane-icao="${escapeHtml(code)}">${escapeHtml(code)}</button>
  `).join(" ");
}


function openAddRouteDialog() {
  const dialog = document.querySelector("#routeDialog");

  if (!dialog) {
    showError("Flight dialog not found.");
    return;
  }

  document.querySelector("#originAirport").value = "";
  document.querySelector("#destinationAirport").value = "";

  const serviceType = getFlightTypeSelect();
  const scheduledTime = document.querySelector("#scheduledTime");

  if (serviceType) {
    serviceType.value = "ON_DEMAND";
  }

  if (scheduledTime) {
    scheduledTime.value = "";
    scheduledTime.disabled = true;
    scheduledTime.required = false;
    scheduledTime.setAttribute("disabled", "disabled");
  }

  document.querySelector("#ticketPrice").value = "0.00";
  document.querySelector("#routePreviewPanel").hidden = true;
  document.querySelector("#routeDialogError").hidden = true;

  setupServiceTypeToggle();

  if (typeof setupFlightTypeExplanation === "function") {
    setupFlightTypeExplanation();
  }

  dialog.showModal();
}

async function previewRoute(options = {}) {
  const payload = routeFormPayload();
  const silent = Boolean(options.silent);
  const error = document.querySelector("#routeDialogError");
  const panel = document.querySelector("#routePreviewPanel");
  const content = document.querySelector("#routePreviewContent");

  error.hidden = true;

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
  } catch (err) {
    if (!silent) {
      panel.hidden = true;
      error.hidden = false;
      error.textContent = err.message || "Unable to preview service.";
    }
  }
}

async function saveRoute(event) {
  event?.preventDefault?.();

  const error = document.querySelector("#routeDialogError");
  error.hidden = true;

  try {
    await postJson(API.create, routeFormPayload());
    document.querySelector("#routeDialog").close();
    await loadRoutes();
  } catch (err) {
    error.hidden = false;
    error.textContent = err.message || "Unable to create flight.";
  }
}

function routeFormPayload() {
  return normalizedFlightFormPayload();
}


function renderPreview(p) {
  return `
    <div class="detail-grid">
      ${section("Air route", [
        ["Route", `${p.origin_airport_icao_code} → ${p.destination_airport_icao_code}`],
        ["Distance", `${p.planned_distance_km} km`],
        ["Duration", `${p.planned_duration_minutes} min`],
        ["Block hours", `${p.block_hours || "-"} h`],
        ["Route layer", "Abstract air route, no aircraft or crew assigned permanently"]
      ])}
      ${section("Flight", [
        ["Service type", "Daily scheduled passenger service"],
        ["Required aircraft class", "LIGHT_COMMERCIAL"],
        ["Airplanes", `${p.aircraft.manufacturer} ${p.aircraft.model_name}`],
        ["Ticket", `${money(p.ticket_price)} ${p.currency_code}`],
        ["Suggested ticket", `${money(p.suggested_ticket_price || 0)} ${p.currency_code}`]
      ])}
      ${section("Expected economics", [
        ["Expected pax", `${p.estimates.expected.passengers} / ${p.passenger_capacity}`],
        ["Revenue", `${money(p.estimates.expected.revenue)} ${p.currency_code}`],
        ["Fuel cost", `${money(p.costs.fuel_cost)} ${p.currency_code}`],
        ["Maintenance reserve", `${money(p.costs.maintenance_cost)} ${p.currency_code}`],
        ["Crew allocated estimate", `${money(p.costs.staff_cost)} ${p.currency_code}`],
        ["Expected profit", `${money(p.estimates.expected.profit)} ${p.currency_code}`]
      ])}
      ${section("Flight note", [
        ["Important", "This does not create a flight yet."],
        ["Dispatch", "Each real flight will later choose a compatible aircraft at departure airport."],
        ["Backup", "If the planned aircraft is away, another compatible aircraft can operate the flight."]
      ])}
    </div>
  `;
}

async function openRouteDetail(serviceId) {
  const dialog = document.querySelector("#routeDetailDialog");
  const title = document.querySelector("#routeDetailTitle");
  const content = document.querySelector("#routeDetailContent");

  title.textContent = "Flight";
  content.textContent = "Loading...";
  dialog.showModal();

  try {
    const data = await getJson(API.detail(serviceId));
    const s = data.service;
    const flights = data.recent_flights || [];

    title.textContent = `${s.service_code}`;

    content.innerHTML = `
      <div class="detail-grid">
        ${section("Air route", [
          ["Flight code", publicFlightCode(s)],
          ["Route", `${s.origin_airport_icao_code} → ${s.destination_airport_icao_code}`],
          ["Origin", `${s.origin_airport_name || "-"} (${s.origin_airport_icao_code})`],
          ["Destination", `${s.destination_airport_name || "-"} (${s.destination_airport_icao_code})`],
          ["Scope", s.route_scope],
          ["Market", s.route_market],
          ["Distance", `${s.planned_distance_km} km`],
          ["Estimated block", `${s.estimated_block_minutes} min`]
        ])}
        ${section("Flight", [
          ["Internal code", s.service_code],
          ["Recurrence", s.recurrence_type],
          ["Scheduled", serviceScheduleLabel(s)],
          ["Service type", s.service_type || "-"],
          ["Airplanes", s.compatible_aircraft_icao_codes || s.compatible_aircraft_model_codes || s.icao_type_code || s.model_code || "-"],
          ["Airplanes", `${s.manufacturer || "-"} ${s.model_name || ""}`],
          ["Base ticket", `${money(s.base_ticket_price)} ${s.currency_code}`]
        ])}
        ${section("Dispatch policy", [
          ["Aircraft binding", "No permanent aircraft binding at route level"],
          ["Dispatch", "Real flight chooses compatible aircraft at origin airport"],
          ["Backup allowed", Number(s.allow_backup_aircraft) ? "Yes" : "No"],
          ["Extra flights allowed", Number(s.allow_extra_flights) ? "Yes" : "No"]
        ])}
        <section class="detail-section">
          <h3>Recent flight instances</h3>
          ${
            flights.length
              ? `<dl class="detail-list">${flights.map(f => `
                  ${detailRow(f.flight_code || `Flight #${f.id}`, `${f.flight_operation_type || "-"} · ${f.status} · dispatch ${f.dispatch_status || "-"} · profit ${money(f.profit_amount)} ${f.currency_code || ""}`)}
                `).join("")}</dl>`
              : `<p class="muted">No real flight instances generated yet for this service.</p>`
          }
        </section>
      </div>
      <div class="dialog-action-bar">
        <button type="button" class="danger" id="removeServiceButton">Remove flight</button>
      </div>
    `;

    const removeButton = content.querySelector("#removeServiceButton");
    if (removeButton) {
      removeButton.addEventListener("click", () => removeService(Number(s.id || s.service_id)));
    }
  } catch (error) {
    content.innerHTML = `<div class="page-error">${escapeHtml(error.message || "Unable to load service detail.")}</div>`;
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
    const m = data.model;

    title.textContent = `${m.icao_type_code} · ${m.manufacturer} ${m.model_name}`;
    content.innerHTML = `
      <div class="model-image-wrap">
        ${m.image_asset_path ? `<img src="${escapeHtml(m.image_asset_path)}" alt="${escapeHtml(m.manufacturer)} ${escapeHtml(m.model_name)}">` : `<p class="muted">No image available.</p>`}
      </div>
      <div class="detail-grid">
        ${section("Identity", [
          ["ICAO type", m.icao_type_code],
          ["Manufacturer", m.manufacturer],
          ["Model", m.model_name],
          ["Internal model code", m.model_code],
          ["Operation role", m.operation_role]
        ])}
        ${section("Performance", [
          ["Passengers", m.passenger_capacity_standard],
          ["Range", `${m.range_km ?? "-"} km`],
          ["Cruise speed", `${m.cruise_speed_kmh ?? "-"} km/h`],
          ["Fuel burn", `${m.fuel_burn_kg_per_hour ?? "-"} kg/h`],
          ["Maintenance cost/h", `${money(m.maintenance_cost_per_hour || 0)}`]
        ])}
        ${section("Economics", [
          ["Indicative new price", `${money(m.new_purchase_price || 0)}`]
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
        <button value="close" class="close-button" aria-label="Close">×</button>
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

async function removeService(serviceId) {
  if (!confirm("Remove this flight? Existing completed flight history will remain, but the flight will be cancelled.")) {
    return;
  }

  try {
    await postJson(API.removeService, { service_id: serviceId });
    document.querySelector("#routeDetailDialog")?.close();
    await loadRoutes();
  } catch (error) {
    alert(error.message || "Unable to remove flight.");
  }
}



function setupFlightTypeExplanation() {
  const serviceType = getFlightTypeSelect();
  const explanation = document.querySelector("#flightTypeExplanation");

  if (!serviceType || !explanation) {
    return;
  }

  const refresh = () => {
    if (serviceType.value === "SCHEDULED") {
      explanation.textContent = "Scheduled flight: recurring planned flight with a fixed UTC departure time. The aircraft must be available at the origin airport when departure time arrives.";
    } else {
      explanation.textContent = "On-demand flight: manual non-scheduled flight that can be started when compatible aircraft and crew are available. Useful for extra income, but it may interfere with later scheduled flights.";
    }
  };

  if (!serviceType.dataset.explanationBound) {
    serviceType.dataset.explanationBound = "true";
    serviceType.addEventListener("change", refresh);
  }

  refresh();
}


function setupServiceTypeToggle() {
  const serviceType = getFlightTypeSelect();
  const scheduledTime = document.querySelector("#scheduledTime");

  if (!serviceType || !scheduledTime) {
    return;
  }

  const refresh = () => {
    const isScheduled = serviceType.value === "SCHEDULED";

    if (isScheduled) {
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
  };

  if (!serviceType.dataset.bound) {
    serviceType.dataset.bound = "true";
    serviceType.addEventListener("change", refresh);
    serviceType.addEventListener("input", refresh);
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

    await previewRoute({ silent: true });
  }, 450);

  origin.addEventListener("input", maybeSuggest);
  destination.addEventListener("input", maybeSuggest);
  origin.addEventListener("blur", maybeSuggest);
  destination.addEventListener("blur", maybeSuggest);
}

function debounce(callback, waitMs) {
  let timeoutId = null;

  return (...args) => {
    window.clearTimeout(timeoutId);
    timeoutId = window.setTimeout(() => callback(...args), waitMs);
  };
}

function section(title, rows) {
  return `<section class="detail-section"><h3>${escapeHtml(title)}</h3><dl class="detail-list">${rows.map(([k,v]) => detailRow(k, v)).join("")}</dl></section>`;
}

async function getJson(url) {
  const response = await fetch(url, { headers: { "Accept": "application/json" }, credentials: "same-origin" });
  const body = await response.json().catch(() => null);
  if (!response.ok) throw new Error(body?.message || body?.error || `Request failed: ${response.status}`);
  return body;
}

async function postJson(url, payload) {
  const response = await fetch(url, { method: "POST", headers: { "Accept": "application/json", "Content-Type": "application/json" }, credentials: "same-origin", body: JSON.stringify(payload) });
  const body = await response.json().catch(() => null);
  if (!response.ok) throw new Error(body?.message || body?.error || `Request failed: ${response.status}`);
  return body;
}

function summaryRow(label, value) { return `<div><dt>${escapeHtml(label)}</dt><dd>${escapeHtml(value ?? "-")}</dd></div>`; }
function detailRow(label, value) { return `<div><dt>${escapeHtml(label)}</dt><dd>${escapeHtml(value ?? "-")}</dd></div>`; }
function startUtcClock() { const c = document.querySelector("#utcClock"); function t(){ c.textContent = new Date().toISOString().replace("T"," ").slice(0,19)+" UTC"; } t(); setInterval(t,1000); }
function money(value) { return Number(value || 0).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 }); }
function showError(message) { const e = document.querySelector("#pageError"); e.hidden = false; e.textContent = message; }
function hideError() { const e = document.querySelector("#pageError"); e.hidden = true; e.textContent = ""; }
function escapeHtml(value) { return String(value ?? "").replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;").replaceAll('"',"&quot;").replaceAll("'","&#039;"); }


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



/*
 * Hard fix for Flight type -> Scheduled departure UTC.
 * This controller is intentionally independent from older setupServiceTypeToggle()
 * versions, because routes.js has been patched many times during migration.
 */
function forceScheduledDepartureController() {
  const serviceType = getFlightTypeSelect();
  const scheduledTime = document.querySelector("#scheduledTime");

  if (!serviceType || !scheduledTime) {
    return;
  }

  const applyState = () => {
    const isScheduled = serviceType.value === "SCHEDULED";

    if (isScheduled) {
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
  };

  if (!serviceType.dataset.hardScheduledControllerBound) {
    serviceType.dataset.hardScheduledControllerBound = "true";

    serviceType.addEventListener("change", () => {
      applyState();
    });

    serviceType.addEventListener("input", () => {
      applyState();
    });
  }

  applyState();
}

document.addEventListener("DOMContentLoaded", () => {
  forceScheduledDepartureController();

  const addButton =
    document.querySelector("#addRouteButton") ||
    document.querySelector("#addFlightButton") ||
    document.querySelector("[data-action='add-flight']");

  if (addButton && !addButton.dataset.scheduledTimeHardFixBound) {
    addButton.dataset.scheduledTimeHardFixBound = "true";
    addButton.addEventListener("click", () => {
      window.setTimeout(forceScheduledDepartureController, 0);
      window.setTimeout(forceScheduledDepartureController, 50);
    });
  }
});

document.addEventListener("click", event => {
  const target = event.target;

  if (!(target instanceof Element)) {
    return;
  }

  if (
    target.matches("#addRouteButton") ||
    target.matches("#addFlightButton") ||
    target.closest("#routeDialog")
  ) {
    window.setTimeout(forceScheduledDepartureController, 0);
  }
});



function normalizedFlightFormPayload() {
  const serviceType = getFlightTypeSelect()?.value || "ON_DEMAND";
  const scheduledTimeField = document.querySelector("#scheduledTime");
  const scheduledTime = serviceType === "SCHEDULED"
    ? (scheduledTimeField?.value || "10:00")
    : "";

  return {
    service_type: serviceType,
    flight_type: serviceType,
    route_category_code: document.querySelector("#routeCategory")?.value || "",
    origin_airport_icao_code: document.querySelector("#originAirport").value.trim().toUpperCase(),
    destination_airport_icao_code: document.querySelector("#destinationAirport").value.trim().toUpperCase(),
    scheduled_departure_time_utc: scheduledTime,
    ticket_price: Number(document.querySelector("#ticketPrice").value)
  };
}

