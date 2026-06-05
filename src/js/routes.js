const API = {
  routes: "api/public/routes/list.php",
  create: "api/public/routes/create.php",
  detail: id => `api/public/routes/detail.php?serviceId=${encodeURIComponent(id)}`,
  preview: "api/public/routes/preview.php"
};

let services = [];
let lastSuggestedTicketPrice = null;

document.addEventListener("DOMContentLoaded", async () => {
  startUtcClock();
  document.querySelector("#refreshButton")?.addEventListener("click", loadRoutes);
  document.querySelector("#addRouteButton")?.addEventListener("click", openAddRouteDialog);
  document.querySelector("#previewRouteButton")?.addEventListener("click", previewRoute);
  document.querySelector("#saveRouteButton")?.addEventListener("click", saveRoute);
  setupTicketSuggestion();
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
    tbody.innerHTML = `<tr><td colspan="8">No scheduled services yet.</td></tr>`;
    return;
  }

  tbody.innerHTML = rows.map(service => `
    <tr>
      <td>
        <strong>${escapeHtml(service.service_code)}</strong>
        <div class="muted">${escapeHtml(service.route_code)}</div>
      </td>
      <td>${escapeHtml(service.origin_airport_icao_code)} → ${escapeHtml(service.destination_airport_icao_code)}</td>
      <td>${escapeHtml(service.scheduled_departure_time_utc || "-")}</td>
      <td>${escapeHtml(service.required_aircraft_class || "-")}</td>
      <td>${escapeHtml(service.manufacturer || "")} ${escapeHtml(service.model_name || "")}</td>
      <td>${money(service.ticket_price)} ${escapeHtml(service.currency_code || "")}</td>
      <td><span class="badge ${service.status === "ACTIVE" ? "good" : "warn"}">${escapeHtml(service.status || "-")}</span></td>
      <td>
        <div class="button-row">
          <button type="button" data-service-detail="${service.service_id}">Details</button>
        </div>
      </td>
    </tr>
  `).join("");

  tbody.querySelectorAll("[data-service-detail]").forEach(button => {
    button.addEventListener("click", () => openRouteDetail(Number(button.dataset.serviceDetail)));
  });
}

function openAddRouteDialog() {
  const dialog = document.querySelector("#routeDialog");

  if (!dialog) {
    showError("Service dialog not found.");
    return;
  }

  document.querySelector("#originAirport").value = "";
  document.querySelector("#destinationAirport").value = "";
  document.querySelector("#scheduledTime").value = "10:00";
  document.querySelector("#ticketPrice").value = "0.00";
  document.querySelector("#routePreviewPanel").hidden = true;
  document.querySelector("#routeDialogError").hidden = true;

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
    error.textContent = err.message || "Unable to create scheduled service.";
  }
}

function routeFormPayload() {
  return {
    origin_airport_icao_code: document.querySelector("#originAirport").value.trim().toUpperCase(),
    destination_airport_icao_code: document.querySelector("#destinationAirport").value.trim().toUpperCase(),
    scheduled_departure_time_utc: document.querySelector("#scheduledTime").value,
    ticket_price: Number(document.querySelector("#ticketPrice").value)
  };
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
      ${section("Scheduled service", [
        ["Service type", "Daily scheduled passenger service"],
        ["Required aircraft class", "LIGHT_COMMERCIAL"],
        ["Preferred model", `${p.aircraft.manufacturer} ${p.aircraft.model_name}`],
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

  title.textContent = "Scheduled service";
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
          ["Route code", s.route_code],
          ["Route", `${s.origin_airport_icao_code} → ${s.destination_airport_icao_code}`],
          ["Origin", `${s.origin_airport_name || "-"} (${s.origin_airport_icao_code})`],
          ["Destination", `${s.destination_airport_name || "-"} (${s.destination_airport_icao_code})`],
          ["Scope", s.route_scope],
          ["Market", s.route_market],
          ["Distance", `${s.planned_distance_km} km`],
          ["Estimated block", `${s.estimated_block_minutes} min`]
        ])}
        ${section("Scheduled service", [
          ["Service code", s.service_code],
          ["Recurrence", s.recurrence_type],
          ["Departure UTC", s.scheduled_departure_time_utc],
          ["Status", s.service_status],
          ["Required aircraft class", s.required_aircraft_class],
          ["Preferred model", `${s.manufacturer || "-"} ${s.model_name || ""}`],
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
    `;
  } catch (error) {
    content.innerHTML = `<div class="page-error">${escapeHtml(error.message || "Unable to load service detail.")}</div>`;
  }
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
