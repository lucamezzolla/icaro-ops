const API = {
  list: page => `api/public/flights/log.php?page=${encodeURIComponent(page)}`,
  detail: id => `api/public/flights/detail.php?flightId=${encodeURIComponent(id)}`
};

const FLIGHT_LOG_PAGE_SIZE = 10;
let currentFlightLogPage = 1;
let currentFlightLogPagination = {
  page: 1,
  page_size: FLIGHT_LOG_PAGE_SIZE,
  total_records: 0,
  total_pages: 1,
  has_previous: false,
  has_next: false
};

document.addEventListener("DOMContentLoaded", async () => {
  startUtcClock();
  document.querySelector("#refreshButton")?.addEventListener("click", () => loadFlightLog(currentFlightLogPage));
  await loadFlightLog(1);
});

async function loadFlightLog(page = 1) {
  hideError();
  try {
    const data = await getJson(API.list(page));
    currentFlightLogPagination = data.pagination || currentFlightLogPagination;
    currentFlightLogPage = Number(currentFlightLogPagination.page || page || 1);
    renderSummary(data.summary || {});
    renderFlights(data.flights || []);
    renderPaginationControls();
  } catch (error) {
    showError(error.message || "Unable to load flight log.");
  }
}


function renderPaginationControls() {
  const top = document.querySelector("#flightLogPaginationTop");
  const bottom = document.querySelector("#flightLogPaginationBottom");

  if (!top && !bottom) {
    return;
  }

  const html = paginationControlsHtml();

  [top, bottom].forEach(container => {
    if (!container) {
      return;
    }

    container.innerHTML = html;

    container.querySelectorAll("[data-flight-log-page]").forEach(button => {
      button.addEventListener("click", () => {
        const page = Number(button.dataset.flightLogPage || 1);
        loadFlightLog(page);
      });
    });
  });
}

function paginationControlsHtml() {
  const page = Number(currentFlightLogPagination.page || 1);
  const pageSize = Number(currentFlightLogPagination.page_size || FLIGHT_LOG_PAGE_SIZE);
  const totalRecords = Number(currentFlightLogPagination.total_records || 0);
  const totalPages = Math.max(1, Number(currentFlightLogPagination.total_pages || 1));
  const firstRecord = totalRecords === 0 ? 0 : ((page - 1) * pageSize) + 1;
  const lastRecord = Math.min(totalRecords, page * pageSize);

  return `
    <div class="pagination-info">
      Page ${page} of ${totalPages} - Records ${firstRecord}-${lastRecord} of ${totalRecords}
    </div>
    <div class="pagination-buttons">
      <button type="button" data-flight-log-page="1" ${page <= 1 ? "disabled" : ""}>First</button>
      <button type="button" data-flight-log-page="${Math.max(1, page - 1)}" ${page <= 1 ? "disabled" : ""}>Previous</button>
      <button type="button" data-flight-log-page="${Math.min(totalPages, page + 1)}" ${page >= totalPages ? "disabled" : ""}>Next</button>
      <button type="button" data-flight-log-page="${totalPages}" ${page >= totalPages ? "disabled" : ""}>Last</button>
    </div>
  `;
}

function renderSummary(summary) {
  document.querySelector("#flightLogSummary").innerHTML = `
    ${summaryRow("Total", summary.total_flights ?? 0)}
    ${summaryRow("Completed", summary.completed_flights ?? 0)}
    ${summaryRow("In flight", summary.in_flight_count ?? 0)}
    ${summaryRow("Net profit", moneyWithCurrency(summary.total_profit_amount ?? 0, summary.currency_code || "EUR"))}
  `;
}

function renderFlights(rows) {
  const tbody = document.querySelector("#flightLogTableBody");
  if (!rows.length) {
    tbody.innerHTML = `<tr><td colspan="8">No flights yet.</td></tr>`;
    return;
  }

  tbody.innerHTML = rows.map(f => `
    <tr>
      <td><strong>${escapeHtml(f.flight_code)}</strong></td>
      <td>${escapeHtml(f.origin_airport_icao_code)} → ${escapeHtml(f.destination_airport_icao_code)}</td>
      <td><span class="badge ${statusClass(f.status)}">${escapeHtml(f.status)}</span></td>
      <td>${escapeHtml(f.actual_departure_at_utc || f.scheduled_departure_at_utc || "-")}</td>
      <td>${escapeHtml(f.actual_arrival_at_utc || f.scheduled_arrival_at_utc || "-")}</td>
      <td>${escapeHtml(f.registration_code || "-")}</td>
      <td class="${profitClass(f.profit_amount)}">${moneyWithCurrency(f.profit_amount, f.currency_code || "EUR")}</td>
      <td><button type="button" data-flight-id="${f.flight_id}">Details</button></td>
    </tr>
  `).join("");

  tbody.querySelectorAll("[data-flight-id]").forEach(button => {
    button.addEventListener("click", () => openFlightDetail(Number(button.dataset.flightId)));
  });
}

async function openFlightDetail(flightId) {
  const dialog = document.querySelector("#flightDetailDialog");
  const title = document.querySelector("#dialogTitle");
  const content = document.querySelector("#flightDetailContent");
  title.textContent = "Flight";
  content.textContent = "Loading...";
  dialog.showModal();

  try {
    const data = await getJson(API.detail(flightId));
    title.textContent = `${data.flight.flight_code} · ${data.flight.origin_airport_icao_code} → ${data.flight.destination_airport_icao_code}`;
    content.innerHTML = renderFlightDetail(data.flight, data.reputation_journal || []);
  } catch (error) {
    content.innerHTML = `<div class="page-error">${escapeHtml(error.message || "Unable to load flight detail.")}</div>`;
  }
}

function renderFlightDetail(f, reputation) {
  return `
    <div class="detail-grid">
      ${section("Flight", [
        ["Flight code", f.flight_code], ["Status", f.status],
        ["Route", `${f.origin_airport_icao_code} → ${f.destination_airport_icao_code}`],
        ["Origin", `${f.origin_airport_name || "-"} (${f.origin_airport_icao_code})`],
        ["Destination", `${f.destination_airport_name || "-"} (${f.destination_airport_icao_code})`],
        ["Flight date UTC", f.flight_date_utc]
      ])}
      ${section("Aircraft", [
        ["Registration", f.registration_code], ["Manufacturer", f.manufacturer],
        ["Model", f.model_name], ["Model code", f.model_code],
        ["ICAO type", f.icao_type_code], ["Cruise speed", `${f.cruise_speed_kmh || "-"} km/h`]
      ])}
      ${section("Timing", [
        ["Scheduled departure", f.scheduled_departure_at_utc],
        ["Scheduled arrival", f.scheduled_arrival_at_utc],
        ["Actual departure", f.actual_departure_at_utc],
        ["Actual arrival", f.actual_arrival_at_utc],
        ["Planned distance", `${f.planned_distance_km || "-"} km`],
        ["Planned duration", `${f.planned_duration_minutes || "-"} min`]
      ])}
      ${section("Passengers", [
        ["Capacity", f.passenger_capacity], ["Passengers", f.passenger_count],
        ["Load factor", `${f.load_factor_percent}%`],
        ["Ticket price", moneyWithCurrency(f.ticket_price, f.currency_code)]
      ])}
      ${section("Financials", [
        ["Revenue", moneyWithCurrency(f.passenger_revenue, f.currency_code)],
        ["Fuel cost", moneyWithCurrency(f.fuel_cost, f.currency_code)],
        ["Maintenance cost", moneyWithCurrency(f.maintenance_cost, f.currency_code)],
        ["Staff cost", moneyWithCurrency(f.staff_cost, f.currency_code)],
        ["Total cost", moneyWithCurrency(f.total_operating_cost, f.currency_code)],
        ["Profit", moneyWithCurrency(f.profit_amount, f.currency_code)]
      ])}
      <section class="detail-section">
        <h3>Reputation</h3>
        ${
          reputation.length
            ? `<dl class="detail-list">${reputation.map(r => `
              ${detailRow("Event", r.event_code)}
              ${detailRow("Change", `${r.reputation_before} → ${r.reputation_after} (${r.reputation_delta})`)}
              ${detailRow("Reason", r.reason)}
            `).join("")}</dl>`
            : `<p class="muted">No reputation journal entry for this flight.</p>`
        }
      </section>
    </div>
  `;
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

function summaryRow(label, value) { return `<div><dt>${escapeHtml(label)}</dt><dd>${escapeHtml(value ?? "-")}</dd></div>`; }
function detailRow(label, value) { return `<div><dt>${escapeHtml(label)}</dt><dd>${escapeHtml(value ?? "-")}</dd></div>`; }

function startUtcClock() {
  const clock = document.querySelector("#utcClock");
  function tick() { clock.textContent = new Date().toISOString().replace("T", " ").slice(0, 19) + " UTC"; }
  tick(); setInterval(tick, 1000);
}

function money(value) { return Number(value || 0).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 }); }
function currencySymbol(currencyCode) {
  const code = String(currencyCode || "EUR").toUpperCase();
  if (code === "EUR") return "€";
  if (code === "USD") return "$";
  return code;
}
function moneyWithCurrency(value, currencyCode) {
  const symbol = currencySymbol(currencyCode);
  return `${symbol} ${money(value)}`;
}
function statusClass(status) {
  const s = String(status || "").toLowerCase().replaceAll("_", "-");
  if (s === "completed") return "completed";
  if (s === "in-flight") return "in-flight";
  if (s.includes("cancel")) return "cancelled";
  if (s.includes("fail") || s.includes("block")) return "failed";
  return "";
}
function profitClass(value) { const n = Number(value || 0); return n > 0 ? "profit-positive" : n < 0 ? "profit-negative" : ""; }
function showError(message) { const e = document.querySelector("#pageError"); e.hidden = false; e.textContent = message; }
function hideError() { const e = document.querySelector("#pageError"); e.hidden = true; e.textContent = ""; }
function escapeHtml(value) {
  return String(value ?? "").replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;").replaceAll('"',"&quot;").replaceAll("'","&#039;");
}
