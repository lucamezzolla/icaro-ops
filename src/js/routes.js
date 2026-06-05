const API = {
  me: "api/public/auth/me.php",
  routes: "api/public/routes/list.php",
  createRoute: "api/public/routes/create.php",
  startFlight: "api/public/flights/start-scheduled.php"
};

document.addEventListener("DOMContentLoaded", async () => {
  startUtcClock();

  document.querySelector("#refreshButton")?.addEventListener("click", loadRoutesPage);

  document.querySelector("#routeForm")?.addEventListener("submit", async event => {
    event.preventDefault();
    await createRoute();
  });

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
    list.innerHTML = `<p class="muted">No routes yet. Create LIRA → LIML at 10:00 UTC to test your first scheduled operation.</p>`;
    return;
  }

  list.innerHTML = rows.map(route => `
    <article class="route-card">
      <h3>${escapeHtml(route.origin_airport_icao_code)} → ${escapeHtml(route.destination_airport_icao_code)}</h3>
      <p>${escapeHtml(route.origin_airport_name)} → ${escapeHtml(route.destination_airport_name)}</p>
      <p>
        <strong>${escapeHtml(route.manufacturer)} ${escapeHtml(route.model_name)}</strong>
        · ${escapeHtml(route.registration_code)}
      </p>
      <p>
        Flight crew:
        ${escapeHtml(route.pilot_1_name || "Not assigned")} /
        ${escapeHtml(route.pilot_2_name || "Not assigned")}
      </p>
      <p>
        Ground maintenance:
        ${escapeHtml(route.technician_name || "Not assigned")}
      </p>
      <div class="route-metrics">
        <div><strong>${escapeHtml(route.scheduled_departure_time_utc)}</strong><span>UTC departure</span></div>
        <div><strong>${escapeHtml(route.planned_distance_km)} km</strong><span>Distance</span></div>
        <div><strong>${escapeHtml(route.planned_duration_minutes)} min</strong><span>Duration</span></div>
        <div><strong>${money(route.ticket_price)} ${escapeHtml(route.currency_code)}</strong><span>Ticket</span></div>
      </div>
      <button type="button" data-start-route="${route.route_id}">Start test flight now</button>
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
}

async function createRoute() {
  hideError();

  const payload = {
    origin_airport_icao_code: document.querySelector("#originAirport").value.trim().toUpperCase(),
    destination_airport_icao_code: document.querySelector("#destinationAirport").value.trim().toUpperCase(),
    scheduled_departure_time_utc: document.querySelector("#scheduledTime").value,
    ticket_price: Number(document.querySelector("#ticketPrice").value)
  };

  try {
    await postJson(API.createRoute, payload);
    await loadRoutesPage();
  } catch (error) {
    showError(error.message || "Unable to create route.");
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
