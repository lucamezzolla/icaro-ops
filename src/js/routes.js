const API = {
  me: "api/public/auth/me.php",
  routes: "api/public/routes/list.php",
  createRoute: "api/public/routes/create.php",
  updateRoute: "api/public/routes/update.php",
  deleteRoute: "api/public/routes/delete.php",
  startFlight: "api/public/flights/start-scheduled.php"
};

let routeEditMode = false;
let editingRouteId = null;

document.addEventListener("DOMContentLoaded", async () => {
  startUtcClock();

  document.querySelector("#refreshButton")?.addEventListener("click", loadRoutesPage);

  document.querySelector("#routeForm")?.addEventListener("submit", async event => {
    event.preventDefault();
    await saveRoute();
  });

  ensureCancelEditButton();
  await loadRoutesPage();
});

async function loadRoutesPage() {
  hideError();

  try {
    const me = await getJson(API.me);
    renderCompany(me);
    await loadRoutes();
  } catch (error) {
    showError(error.message || "Unable to load routes page.");
  }
}

function renderCompany(me) {
  document.querySelector("#companySummary").innerHTML = `
    ${summaryRow("Owner", me.owner_name)}
    ${summaryRow("Company", me.company_name)}
    ${summaryRow("Budget", `${money(me.budget_amount)} ${me.currency_code}`)}
    ${summaryRow("Base", `${me.base_airport.icao_code}${me.base_airport.iata_code ? " / " + me.base_airport.iata_code : ""}`)}
  `;
}

async function loadRoutes() {
  const rows = await getJson(API.routes);
  const list = document.querySelector("#routesList");

  if (!rows.length) {
    list.innerHTML = `<p class="muted">No routes yet. Create a daily route to start scheduled operations.</p>`;
    return;
  }

  list.innerHTML = rows.map(route => `
    <article class="route-card">
      <h3>${escapeHtml(route.origin_airport_icao_code)} → ${escapeHtml(route.destination_airport_icao_code)}</h3>
      <p>${escapeHtml(route.origin_airport_name)} → ${escapeHtml(route.destination_airport_name)}</p>
      <p>
        <strong>${escapeHtml(route.manufacturer || "Aircraft")}${route.model_name ? " " + escapeHtml(route.model_name) : ""}</strong>
        ${route.registration_code ? `· ${escapeHtml(route.registration_code)}` : "· No aircraft assigned"}
      </p>
      <p>
        Flight crew:
        ${escapeHtml(route.pilot_1_name || "Not assigned")} /
        ${escapeHtml(route.pilot_2_name || "Not assigned")}
      </p>
      <p>
        Dispatch:
        ${escapeHtml(route.dispatch_readiness || "-")}
      </p>
      <div class="route-metrics">
        <div><strong>${escapeHtml(route.scheduled_departure_time_utc)}</strong><span>UTC departure</span></div>
        <div><strong>${escapeHtml(route.planned_distance_km)} km</strong><span>Distance</span></div>
        <div><strong>${escapeHtml(route.planned_duration_minutes)} min</strong><span>Duration</span></div>
        <div><strong>${money(route.ticket_price)} ${escapeHtml(route.currency_code)}</strong><span>Ticket</span></div>
      </div>
      <div class="route-actions">
        <button type="button" data-start-route="${route.route_id}">Start test flight now</button>
        <button type="button" data-edit-route="${route.route_id}">Edit</button>
        <button type="button" data-delete-route="${route.route_id}">Delete</button>
      </div>
    </article>
  `).join("");

  list.querySelectorAll("[data-start-route]").forEach(button => {
    button.addEventListener("click", async () => {
      const routeId = Number(button.dataset.startRoute);

      if (!confirm("Start this scheduled flight now for testing?")) {
        return;
      }

      try {
        const flight = await postJson(API.startFlight, {
          route_id: routeId,
          force_now: true
        });

        alert(`Flight ${flight.flight_code} is now in flight. Passengers: ${flight.passenger_count}/${flight.passenger_capacity}.`);
        await loadRoutesPage();
      } catch (error) {
        showError(error.message || "Unable to start flight.");
      }
    });
  });

  list.querySelectorAll("[data-edit-route]").forEach(button => {
    button.addEventListener("click", () => {
      const route = rows.find(item => Number(item.route_id) === Number(button.dataset.editRoute));
      if (route) {
        startEditRoute(route);
      }
    });
  });

  list.querySelectorAll("[data-delete-route]").forEach(button => {
    button.addEventListener("click", async () => {
      const routeId = Number(button.dataset.deleteRoute);
      const route = rows.find(item => Number(item.route_id) === routeId);

      if (!confirm(`Delete route ${route?.origin_airport_icao_code || ""} → ${route?.destination_airport_icao_code || ""}?`)) {
        return;
      }

      try {
        const result = await postJson(API.deleteRoute, { route_id: routeId });
        alert(`Route ${result.action.toLowerCase()}.`);
        resetRouteForm();
        await loadRoutesPage();
      } catch (error) {
        showError(error.message || "Unable to delete route.");
      }
    });
  });
}

async function saveRoute() {
  hideError();

  const payload = {
    origin_airport_icao_code: document.querySelector("#originAirport").value.trim().toUpperCase(),
    destination_airport_icao_code: document.querySelector("#destinationAirport").value.trim().toUpperCase(),
    scheduled_departure_time_utc: document.querySelector("#scheduledTime").value,
    ticket_price: Number(document.querySelector("#ticketPrice").value)
  };

  try {
    if (routeEditMode && editingRouteId) {
      await postJson(API.updateRoute, {
        ...payload,
        route_id: editingRouteId
      });
    } else {
      await postJson(API.createRoute, payload);
    }

    resetRouteForm();
    await loadRoutesPage();
  } catch (error) {
    showError(error.message || "Unable to save route.");
  }
}

function startEditRoute(route) {
  routeEditMode = true;
  editingRouteId = Number(route.route_id);

  document.querySelector("#originAirport").value = route.origin_airport_icao_code || "";
  document.querySelector("#destinationAirport").value = route.destination_airport_icao_code || "";
  document.querySelector("#scheduledTime").value = String(route.scheduled_departure_time_utc || "").slice(0, 5);
  document.querySelector("#ticketPrice").value = Number(route.ticket_price || 0);

  const submitButton = document.querySelector('#routeForm button[type="submit"]');
  if (submitButton) {
    submitButton.textContent = "Save route changes";
  }

  const cancelButton = document.querySelector("#cancelEditRouteButton");
  if (cancelButton) {
    cancelButton.hidden = false;
  }

  document.querySelector("#routeForm").scrollIntoView({
    behavior: "smooth",
    block: "center"
  });
}

function resetRouteForm() {
  routeEditMode = false;
  editingRouteId = null;

  document.querySelector("#routeForm")?.reset();

  const submitButton = document.querySelector('#routeForm button[type="submit"]');
  if (submitButton) {
    submitButton.textContent = "Create daily route";
  }

  const cancelButton = document.querySelector("#cancelEditRouteButton");
  if (cancelButton) {
    cancelButton.hidden = true;
  }
}

function ensureCancelEditButton() {
  const form = document.querySelector("#routeForm");
  if (!form || document.querySelector("#cancelEditRouteButton")) {
    return;
  }

  const button = document.createElement("button");
  button.id = "cancelEditRouteButton";
  button.type = "button";
  button.textContent = "Cancel edit";
  button.hidden = true;
  button.addEventListener("click", resetRouteForm);

  form.appendChild(button);
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
  return `
    <div>
      <dt>${escapeHtml(label)}</dt>
      <dd>${escapeHtml(value ?? "-")}</dd>
    </div>
  `;
}

function startUtcClock() {
  const clock = document.querySelector("#utcClock");

  function tick() {
    const now = new Date();
    clock.textContent = now.toISOString().replace("T", " ").slice(0, 19) + " UTC";
  }

  tick();
  setInterval(tick, 1000);
}

function money(value) {
  const numeric = Number(value ?? 0);
  return numeric.toLocaleString("en-US", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  });
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
