const API = {
  routes: "api/public/routes/list.php",
  create: "api/public/routes/create.php",
  detail: id => `api/public/routes/detail.php?routeId=${encodeURIComponent(id)}`,
  preview: "api/public/routes/preview.php",
  startFlight: "api/public/flights/start-scheduled.php"
};

let routes = [];

document.addEventListener("DOMContentLoaded", async () => {
  startUtcClock();
  document.querySelector("#refreshButton")?.addEventListener("click", loadRoutes);
  document.querySelector("#addRouteButton")?.addEventListener("click", openAddRouteDialog);
  document.querySelector("#previewRouteButton")?.addEventListener("click", previewRoute);
  document.querySelector("#saveRouteButton")?.addEventListener("click", saveRoute);
  await loadRoutes();
});

async function loadRoutes() {
  hideError();
  try {
    routes = await getJson(API.routes);
    renderSummary(routes);
    renderRoutes(routes);
  } catch (error) {
    showError(error.message || "Unable to load routes.");
  }
}

function renderSummary(rows) {
  const active = rows.filter(r => r.status === "ACTIVE").length;
  const ready = rows.filter(r => r.dispatch_readiness === "READY").length;
  document.querySelector("#routesSummary").innerHTML = `
    ${summaryRow("Total", rows.length)}
    ${summaryRow("Active", active)}
    ${summaryRow("Ready", ready)}
  `;
}

function renderRoutes(rows) {
  const tbody = document.querySelector("#routesTableBody");
  if (!rows.length) {
    tbody.innerHTML = `<tr><td colspan="8">No routes yet.</td></tr>`;
    return;
  }

  tbody.innerHTML = rows.map(route => `
    <tr>
      <td><strong>${escapeHtml(route.origin_airport_icao_code)} → ${escapeHtml(route.destination_airport_icao_code)}</strong></td>
      <td>${escapeHtml(route.scheduled_departure_time_utc || "-")}</td>
      <td>${escapeHtml(route.registration_code || "Unassigned")}</td>
      <td>${escapeHtml(route.pilot_1_name || "-")} / ${escapeHtml(route.pilot_2_name || "-")}</td>
      <td>${escapeHtml(route.planned_duration_minutes || "-")} min</td>
      <td>${money(route.ticket_price)} ${escapeHtml(route.currency_code || "")}</td>
      <td><span class="badge ${route.dispatch_readiness === "READY" ? "good" : "warn"}">${escapeHtml(route.dispatch_readiness || route.status || "-")}</span></td>
      <td>
        <div class="button-row">
          <button type="button" data-route-detail="${route.route_id}">Details</button>
          <button type="button" data-start-route="${route.route_id}" class="secondary">Start</button>
        </div>
      </td>
    </tr>
  `).join("");

  tbody.querySelectorAll("[data-route-detail]").forEach(button => {
    button.addEventListener("click", () => openRouteDetail(Number(button.dataset.routeDetail)));
  });

  tbody.querySelectorAll("[data-start-route]").forEach(button => {
    button.addEventListener("click", async () => {
      if (!confirm("Start this scheduled flight now for testing?")) return;
      try {
        const flight = await postJson(API.startFlight, { route_id: Number(button.dataset.startRoute), force_now: true });
        alert(`Flight ${flight.flight_code} is now in flight.`);
        await loadRoutes();
      } catch (error) {
        showError(error.message || "Unable to start flight.");
      }
    });
  });
}

function openAddRouteDialog() {
  const dialog = document.querySelector("#routeDialog");

  if (!dialog) {
    showError("Route dialog not found.");
    return;
  }

  document.querySelector("#originAirport").value = "";
  document.querySelector("#destinationAirport").value = "";
  document.querySelector("#scheduledTime").value = "10:00";
  document.querySelector("#ticketPrice").value = "250.00";
  document.querySelector("#routePreviewPanel").hidden = true;
  document.querySelector("#routeDialogError").hidden = true;

  dialog.showModal();
}

async function previewRoute() {
  const payload = routeFormPayload();
  const error = document.querySelector("#routeDialogError");
  const panel = document.querySelector("#routePreviewPanel");
  const content = document.querySelector("#routePreviewContent");

  error.hidden = true;
  panel.hidden = false;
  content.textContent = "Calculating preview...";

  try {
    const preview = await postJson(API.preview, payload);
    content.innerHTML = renderPreview(preview);
  } catch (err) {
    panel.hidden = true;
    error.hidden = false;
    error.textContent = err.message || "Unable to preview route.";
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
    error.textContent = err.message || "Unable to create route.";
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
      ${section("Route", [
        ["Route", `${p.origin_airport_icao_code} → ${p.destination_airport_icao_code}`],
        ["Distance", `${p.planned_distance_km} km`],
        ["Duration", `${p.planned_duration_minutes} min`],
        ["Block hours", `${p.block_hours} h`],
        ["Aircraft", `${p.aircraft.manufacturer} ${p.aircraft.model_name}`]
      ])}
      ${section("Passengers", [
        ["Capacity", p.passenger_capacity],
        ["Low estimate", `${p.estimates.low.passengers} pax · revenue ${money(p.estimates.low.revenue)} · profit ${money(p.estimates.low.profit)} ${p.currency_code}`],
        ["Expected", `${p.estimates.expected.passengers} pax · revenue ${money(p.estimates.expected.revenue)} · profit ${money(p.estimates.expected.profit)} ${p.currency_code}`],
        ["High estimate", `${p.estimates.high.passengers} pax · revenue ${money(p.estimates.high.revenue)} · profit ${money(p.estimates.high.profit)} ${p.currency_code}`]
      ])}
      ${section("Expected economics", [
        ["Revenue", `${money(p.estimates.expected.revenue)} ${p.currency_code}`],
        ["Fuel cost", `${money(p.costs.fuel_cost)} ${p.currency_code}`],
        ["Maintenance reserve", `${money(p.costs.maintenance_cost)} ${p.currency_code}`],
        ["Crew allocated cost", `${money(p.costs.staff_cost)} ${p.currency_code}`],
        ["Total cost", `${money(p.costs.total_operating_cost)} ${p.currency_code}`],
        ["Expected profit", `${money(p.estimates.expected.profit)} ${p.currency_code}`]
      ])}
      ${section("Pricing", [
        ["Current ticket", `${money(p.ticket_price)} ${p.currency_code}`],
        ["Suggested ticket", `${money(p.suggested_ticket_price)} ${p.currency_code}`],
        ["Break-even pax", p.break_even_passengers],
        ["Recommendation", p.recommendation]
      ])}
      ${section("Cost model", [
        ["Crew formula", p.cost_model?.crew_cost_formula || "-"],
        ["Crew base before share", `${money(p.cost_model?.crew_base_cost_before_revenue_share || 0)} ${p.currency_code}`],
        ["Daily retainer", p.cost_model?.daily_retainer_note || "-"],
        ["Fuel burn", `${p.aircraft.fuel_burn_kg_per_hour} kg/h`],
        ["Cruise speed", `${p.aircraft.cruise_speed_kmh} km/h`]
      ])}
    </div>
  `;
}

async function openRouteDetail(routeId) {
  const dialog = document.querySelector("#routeDetailDialog");
  const title = document.querySelector("#routeDetailTitle");
  const content = document.querySelector("#routeDetailContent");
  title.textContent = "Route";
  content.textContent = "Loading...";
  dialog.showModal();

  try {
    const data = await getJson(API.detail(routeId));
    const r = data.route;
    title.textContent = `${r.origin_airport_icao_code} → ${r.destination_airport_icao_code}`;
    content.innerHTML = `
      <div class="detail-grid">
        ${section("Route", [
          ["Route ID", r.route_id],
          ["Status", r.status],
          ["Origin", `${r.origin_airport_name} (${r.origin_airport_icao_code})`],
          ["Destination", `${r.destination_airport_name} (${r.destination_airport_icao_code})`],
          ["Departure UTC", r.scheduled_departure_time_utc],
          ["Recurrence", r.recurrence_type],
          ["Auto dispatch", r.auto_dispatch_enabled],
          ["Backup aircraft", r.allow_backup_aircraft]
        ])}
        ${section("Aircraft", [
          ["Registration", r.registration_code || "-"],
          ["Manufacturer", r.manufacturer || "-"],
          ["Model", r.model_name || "-"],
          ["ICAO type", r.icao_type_code || "-"]
        ])}
        ${section("Crew", [
          ["Pilot 1", r.pilot_1_name || "-"],
          ["Pilot 2", r.pilot_2_name || "-"],
          ["Ground maintenance", r.technician_name || "Not assigned"]
        ])}
        ${section("Economics", [
          ["Distance", `${r.planned_distance_km} km`],
          ["Duration", `${r.planned_duration_minutes} min`],
          ["Ticket", `${money(r.ticket_price)} ${r.currency_code}`],
          ["Dispatch readiness", r.dispatch_readiness]
        ])}
      </div>
    `;
  } catch (error) {
    content.innerHTML = `<div class="page-error">${escapeHtml(error.message || "Unable to load route detail.")}</div>`;
  }
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
