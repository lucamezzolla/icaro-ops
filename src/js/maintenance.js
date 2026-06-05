const API = {
  aircraft: aircraftId => `api/public/maintenance/aircraft.php?aircraftId=${encodeURIComponent(aircraftId)}`,
  schedule: "api/public/maintenance/schedule.php",
  complete: "api/public/maintenance/complete.php"
};

let aircraftId = null;
let currentAircraft = null;

document.addEventListener("DOMContentLoaded", async () => {
  startUtcClock();

  aircraftId = new URLSearchParams(window.location.search).get("aircraftId");

  document.querySelector("#refreshButton")?.addEventListener("click", loadPage);
  document.querySelector("#scheduleMaintenanceButton")?.addEventListener("click", scheduleMaintenance);
  document.querySelector("#completeMaintenanceButton")?.addEventListener("click", completeMaintenance);

  if (!aircraftId) {
    showError("Missing aircraftId.");
    return;
  }

  await loadPage();
});

async function loadPage() {
  hideError();

  try {
    const data = await getJson(API.aircraft(aircraftId));
    currentAircraft = data.aircraft;
    renderAircraft(data.aircraft);
    renderEvents(data.events);
  } catch (error) {
    showError(error.message || "Unable to load maintenance page.");
  }
}

function renderAircraft(a) {
  document.title = `Icaro Ops - ${a.registration_code} Maintenance`;
  document.querySelector("#pageTitle").textContent = `${a.registration_code} maintenance`;

  document.querySelector("#aircraftSummary").innerHTML = `
    ${summaryRow("Aircraft", a.registration_code)}
    ${summaryRow("Model", `${a.manufacturer} ${a.model_name}`)}
    ${summaryRow("Status", a.aircraft_status)}
    ${summaryRow("State", a.maintenance_state)}
    ${summaryRow("Airport", a.current_airport_icao_code)}
  `;

  document.querySelector("#maintenanceDetail").innerHTML = `
    <p>
      <span class="badge ${badgeClass(a.maintenance_state)}">${escapeHtml(a.maintenance_state)}</span>
      <span class="badge">${escapeHtml(a.aircraft_status)}</span>
      <span class="badge">${escapeHtml(a.current_airport_icao_code)}</span>
    </p>

    <div class="metrics">
      <div><strong>${escapeHtml(a.condition_percent)}%</strong><span>Condition</span></div>
      <div><strong>${escapeHtml(a.airframe_hours)}</strong><span>Airframe hours</span></div>
      <div><strong>${escapeHtml(a.cycles_count)}</strong><span>Cycles</span></div>
      <div><strong>${escapeHtml(a.open_event_count)}</strong><span>Open events</span></div>
      <div><strong>${escapeHtml(a.routine_maintenance_interval_hours)} h</strong><span>Routine interval</span></div>
      <div><strong>${escapeHtml(a.routine_maintenance_interval_cycles)}</strong><span>Cycle interval</span></div>
      <div><strong>${escapeHtml(a.condition_warning_threshold_percent)}%</strong><span>Warning threshold</span></div>
      <div><strong>${escapeHtml(a.condition_grounding_threshold_percent)}%</strong><span>Grounding threshold</span></div>
    </div>

    <p><strong>Required technician license:</strong> ${escapeHtml(a.technician_license_required || "-")}</p>
    <p><strong>Current airport:</strong> ${escapeHtml(a.current_airport_name)} (${escapeHtml(a.current_airport_icao_code)})</p>
    <p><strong>Home base:</strong> ${escapeHtml(a.home_base_name)} (${escapeHtml(a.home_base_icao_code)})</p>
  `;

  document.querySelector("#scheduleMaintenanceButton").disabled =
    a.aircraft_status === "IN_FLIGHT" || a.aircraft_status === "MAINTENANCE";

  document.querySelector("#completeMaintenanceButton").disabled =
    a.aircraft_status !== "MAINTENANCE";
}

function renderEvents(rows) {
  const list = document.querySelector("#eventsList");

  if (!rows.length) {
    list.innerHTML = `<p class="muted">No maintenance events yet.</p>`;
    return;
  }

  list.innerHTML = `<div class="event-list">${rows.map(event => `
    <article class="event-card">
      <h3>${escapeHtml(event.title)}</h3>
      <p>
        <span class="badge ${event.severity.toLowerCase()}">${escapeHtml(event.severity)}</span>
        <span class="badge">${escapeHtml(event.event_type)}</span>
        <span class="badge">${escapeHtml(event.status)}</span>
      </p>
      <p>${escapeHtml(event.description)}</p>
      <p><strong>Started:</strong> ${escapeHtml(event.started_at_utc)}</p>
      <p><strong>Estimated done:</strong> ${escapeHtml(event.estimated_completed_at_utc || "-")}</p>
      <p><strong>Completed:</strong> ${escapeHtml(event.completed_at_utc || "-")}</p>
    </article>
  `).join("")}</div>`;
}

async function scheduleMaintenance() {
  if (!currentAircraft) return;

  if (!confirm(`Schedule maintenance for ${currentAircraft.registration_code}?`)) {
    return;
  }

  try {
    await postJson(API.schedule, { aircraft_id: Number(currentAircraft.aircraft_id) });
    await loadPage();
  } catch (error) {
    showError(error.message || "Unable to schedule maintenance.");
  }
}

async function completeMaintenance() {
  if (!currentAircraft) return;

  if (!confirm(`Complete maintenance for ${currentAircraft.registration_code}?`)) {
    return;
  }

  try {
    await postJson(API.complete, { aircraft_id: Number(currentAircraft.aircraft_id) });
    await loadPage();
  } catch (error) {
    showError(error.message || "Unable to complete maintenance.");
  }
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

function badgeClass(state) {
  if (state === "OK") return "ok";
  if (String(state).includes("WARNING") || String(state).includes("DUE")) return "warning";
  if (String(state).includes("GROUNDED") || String(state).includes("IN_FLIGHT")) return "critical";
  return "";
}

function startUtcClock() {
  const clock = document.querySelector("#utcClock");
  function tick() {
    clock.textContent = new Date().toISOString().replace("T", " ").slice(0, 19) + " UTC";
  }
  tick();
  setInterval(tick, 1000);
}

function showError(message) {
  const error = document.querySelector("#pageError");
  error.hidden = false;
  error.textContent = message;
}

function hideError() {
  const error = document.querySelector("#pageError");
  error.hidden = true;
  error.textContent = "";
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}
