const API = {
  fleet: "api/public/fleet/my-aircraft.php",
  catalog: "api/public/fleet/catalog.php",
  detail: id => `api/public/fleet/detail.php?aircraftId=${encodeURIComponent(id)}`,
  buyNew: "api/public/fleet/buy-new.php"
};

let ownedAircraft = [];
let catalogAircraft = [];

document.addEventListener("DOMContentLoaded", async () => {
  startUtcClock();
  document.querySelector("#refreshButton")?.addEventListener("click", loadFleet);
  document.querySelector("#buyAircraftButton")?.addEventListener("click", openBuyDialog);
  await loadFleet();
});

async function loadFleet() {
  hideFleetMessages();

  try {
    const data = await getJson(API.fleet);
    ownedAircraft = data.aircraft || [];
    renderSummary(data.summary || {}, ownedAircraft);
    renderFleetTable(ownedAircraft);
  } catch (error) {
    showFleetError(error.message || "Unable to load fleet.");
  }
}

function renderSummary(summary, rows) {
  const available = rows.filter(a => a.status === "AVAILABLE" || a.status === "PARKED").length;
  const inFlight = rows.filter(a => a.status === "IN_FLIGHT").length;
  const maintenance = rows.filter(a => a.status === "MAINTENANCE").length;

  document.querySelector("#fleetSummary").innerHTML = `
    ${summaryRow("Aircraft", summary.total_aircraft ?? rows.length)}
    ${summaryRow("Available", available)}
    ${summaryRow("In flight", inFlight)}
    ${summaryRow("Maintenance", maintenance)}
    ${summaryRow("Pilot pool", `${summary.qualified_pilots ?? "-"} / ${summary.required_pilots_for_current_fleet ?? "-"}`)}
  `;
}

function renderFleetTable(rows) {
  const tbody = document.querySelector("#fleetTableBody");

  if (!rows.length) {
    tbody.innerHTML = `<tr><td colspan="8">No owned aircraft yet.</td></tr>`;
    return;
  }

  tbody.innerHTML = rows.map(a => `
    <tr>
      <td><strong>${escapeHtml(a.registration_code)}</strong></td>
      <td>${escapeHtml(a.manufacturer)} ${escapeHtml(a.model_name)}</td>
      <td><span class="badge ${statusClass(a.status)}">${escapeHtml(a.status)}</span></td>
      <td>${escapeHtml(a.current_airport_icao_code || "-")}</td>
      <td class="${conditionClass(a.condition_percent)}">${escapeHtml(a.condition_percent ?? "-")}%</td>
      <td>${escapeHtml(a.airframe_hours ?? "0")}</td>
      <td>${escapeHtml(a.cycles_count ?? "0")}</td>
      <td>
        <div class="button-row">
          <button type="button" data-aircraft-detail="${a.aircraft_id}">Details</button>
          <button type="button" data-aircraft-image="${a.aircraft_id}" class="secondary">Image</button>
          <a class="button-link" href="maintenance.html?aircraftId=${encodeURIComponent(a.aircraft_id)}">Maintenance</a>
        </div>
      </td>
    </tr>
  `).join("");

  tbody.querySelectorAll("[data-aircraft-detail]").forEach(button => {
    button.addEventListener("click", () => openAircraftDetail(Number(button.dataset.aircraftDetail)));
  });

  tbody.querySelectorAll("[data-aircraft-image]").forEach(button => {
    button.addEventListener("click", () => openAircraftImage(Number(button.dataset.aircraftImage)));
  });
}

async function openAircraftDetail(aircraftId) {
  const dialog = document.querySelector("#aircraftDetailDialog");
  const title = document.querySelector("#aircraftDetailTitle");
  const content = document.querySelector("#aircraftDetailContent");

  title.textContent = "Aircraft";
  content.textContent = "Loading...";
  dialog.showModal();

  try {
    const data = await getJson(API.detail(aircraftId));
    const a = data.aircraft;
    title.textContent = `${a.registration_code} · ${a.manufacturer} ${a.model_name}`;
    content.innerHTML = renderAircraftDetail(a, data.recent_flights || []);
  } catch (error) {
    content.innerHTML = `<div class="page-error">${escapeHtml(error.message || "Unable to load aircraft detail.")}</div>`;
  }
}

function renderAircraftDetail(a, recentFlights) {
  return `
    <div class="detail-grid">
      ${section("Identity", [
        ["Registration", a.registration_code],
        ["Serial", a.serial_number],
        ["Aircraft", `${a.manufacturer} ${a.model_name}`],
        ["Model code", a.model_code],
        ["ICAO type", a.icao_type_code],
        ["Operation role", a.operation_role]
      ])}
      ${section("Status", [
        ["Status", a.status],
        ["Home base", a.home_base_icao_code],
        ["Current airport", a.current_airport_icao_code],
        ["Condition", `${a.condition_percent}%`],
        ["Airframe hours", a.airframe_hours],
        ["Cycles", a.cycles_count]
      ])}
      ${section("Performance", [
        ["Passenger capacity", a.passenger_capacity_standard],
        ["Range", `${a.range_km} km`],
        ["Cruise speed", `${a.cruise_speed_kmh} km/h`],
        ["Fuel burn", `${a.fuel_burn_kg_per_hour} kg/h`],
        ["Maintenance cost/h", `${money(a.maintenance_cost_per_hour)} ${a.currency_code || "EUR"}`]
      ])}
      ${section("Financial", [
        ["Ownership", a.ownership_status],
        ["Acquisition", a.acquisition_type],
        ["Purchase price", `${money(a.purchase_price)} ${a.currency_code || "EUR"}`],
        ["Market value", `${money(a.current_market_value)} ${a.currency_code || "EUR"}`]
      ])}
      <section class="detail-section">
        <h3>Recent flights</h3>
        ${
          recentFlights.length
            ? `<dl class="detail-list">${recentFlights.map(f => `
              ${detailRow(f.flight_code, `${f.origin_airport_icao_code} → ${f.destination_airport_icao_code} · ${f.status} · ${money(f.profit_amount)} ${f.currency_code}`)}
            `).join("")}</dl>`
            : `<p class="muted">No recent flights found.</p>`
        }
      </section>
      <section class="detail-section">
        <h3>Pilot coverage</h3>
        <p class="muted">
          This aircraft does not have permanently assigned pilots. It is covered by the company pool of active qualified pilots.
          Dispatch will use available qualified pilots for each flight.
        </p>
      </section>
    </div>
  `;
}

function openAircraftImage(aircraftId) {
  const a = ownedAircraft.find(item => Number(item.aircraft_id) === Number(aircraftId));
  if (!a) return;

  const dialog = document.querySelector("#aircraftImageDialog");
  document.querySelector("#aircraftImageTitle").textContent = `${a.manufacturer} ${a.model_name}`;
  const img = document.querySelector("#aircraftImagePreview");
  img.src = a.image_asset_path || "";
  img.alt = `${a.manufacturer} ${a.model_name}`;
  dialog.showModal();
}

async function openBuyDialog() {
  const dialog = document.querySelector("#buyAircraftDialog");
  const list = document.querySelector("#aircraftCatalogList");
  document.querySelector("#buyAircraftError").hidden = true;
  list.textContent = "Loading catalog...";
  dialog.showModal();

  try {
    const data = await getJson(API.catalog);
    catalogAircraft = data.aircraft || [];
    renderCatalog(catalogAircraft, data.pilot_coverage || {});
  } catch (error) {
    list.innerHTML = `<div class="page-error">${escapeHtml(error.message || "Unable to load aircraft catalog.")}</div>`;
  }
}

function renderCatalog(rows, pilotCoverage) {
  const list = document.querySelector("#aircraftCatalogList");

  if (!rows.length) {
    list.innerHTML = `<p class="muted">No aircraft catalog entries available.</p>`;
    return;
  }

  list.innerHTML = `
    <div class="info-box">
      <strong>Current pilot coverage</strong>
      <p>
        Qualified pilots: ${escapeHtml(pilotCoverage.current_qualified_pilots ?? "-")}.
        Required for current fleet: ${escapeHtml(pilotCoverage.required_pilots_for_current_fleet ?? "-")}.
      </p>
    </div>
    <div class="catalog-grid">
      ${rows.map(a => `
        <article class="catalog-card">
          <h3>${escapeHtml(a.manufacturer)} ${escapeHtml(a.model_name)}</h3>
          <p>${escapeHtml(a.model_code)} · ${escapeHtml(a.icao_type_code)} · ${escapeHtml(a.operation_role || "-")}</p>
          <p>Capacity: <strong>${escapeHtml(a.passenger_capacity_standard)}</strong> · Range: <strong>${escapeHtml(a.range_km)} km</strong></p>
          <p>Price: <strong>${money(a.new_purchase_price || a.estimated_new_price || a.purchase_price || 0)} ${escapeHtml(a.currency_code || "EUR")}</strong></p>
          <p class="muted">After purchase pilot need: ${escapeHtml(a.required_pilots_after_purchase ?? "-")} · Current qualified: ${escapeHtml(a.current_qualified_pilots ?? "-")}</p>
          <div class="catalog-actions">
            <button type="button" data-buy-model="${a.aircraft_model_id || a.id}">Buy new</button>
          </div>
        </article>
      `).join("")}
    </div>
  `;

  list.querySelectorAll("[data-buy-model]").forEach(button => {
    button.addEventListener("click", () => buyAircraft(Number(button.dataset.buyModel)));
  });
}

async function buyAircraft(aircraftModelId) {
  const error = document.querySelector("#buyAircraftError");
  error.hidden = true;
  error.textContent = "";

  if (!confirm("Buy this aircraft?")) {
    return;
  }

  try {
    const result = await fleetPostJsonWithVisibleErrors(API.buyNew, { aircraft_model_id: aircraftModelId }, error);
    showFleetSuccess(`Aircraft purchased: ${result.registration_code || "new aircraft"}`);
    document.querySelector("#buyAircraftDialog").close();
    await loadFleet();
  } catch (err) {
    error.hidden = false;
    error.textContent = err.message || "Unable to buy aircraft.";
  }
}

async function getJson(url) {
  const response = await fetch(url, { headers: { "Accept": "application/json" }, credentials: "same-origin" });
  const body = await response.json().catch(() => null);
  if (!response.ok) throw new Error(body?.message || body?.error || `Request failed: ${response.status}`);
  return body;
}

async function fleetPostJsonWithVisibleErrors(url, payload, targetBox = null) {
  hideFleetMessages();

  const response = await fetch(url, {
    method: "POST",
    headers: { "Accept": "application/json", "Content-Type": "application/json" },
    credentials: "same-origin",
    body: JSON.stringify(payload)
  });

  const body = await response.json().catch(() => null);

  if (!response.ok) {
    const lines = [];
    const code = body?.error || `HTTP_${response.status}`;

    if (code === "INSUFFICIENT_QUALIFIED_PILOTS") {
      lines.push("Pilot coverage is not sufficient for this purchase.");
      lines.push("Pilots are a qualified company pool, not assigned permanently to a single aircraft.");
    } else {
      lines.push(body?.message || code || `Request failed: ${response.status}`);
    }

    if (body?.required_pilots_after_purchase !== undefined) {
      lines.push(`Required qualified pilots after purchase: ${body.required_pilots_after_purchase}`);
    }

    if (body?.current_qualified_pilots !== undefined) {
      lines.push(`Current qualified pilots: ${body.current_qualified_pilots}`);
    }

    if (body?.required_license) {
      lines.push(`Required aircraft qualification: ${body.required_license}`);
    }

    const message = lines.join("\n");

    if (targetBox) {
      targetBox.hidden = false;
      targetBox.textContent = message;
    } else {
      showFleetError(message);
    }

    throw new Error(message);
  }

  return body;
}

function showFleetError(message) {
  const box = document.querySelector("#fleetPageError");
  if (!box) return;
  box.hidden = false;
  box.textContent = message;
}

function showFleetSuccess(message) {
  const box = document.querySelector("#fleetPageSuccess");
  if (!box) return;
  box.hidden = false;
  box.textContent = message;
}

function hideFleetMessages() {
  for (const selector of ["#fleetPageError", "#fleetPageSuccess"]) {
    const box = document.querySelector(selector);
    if (box) {
      box.hidden = true;
      box.textContent = "";
    }
  }
}

function section(title, rows) {
  return `<section class="detail-section"><h3>${escapeHtml(title)}</h3><dl class="detail-list">${rows.map(([k,v]) => detailRow(k, v)).join("")}</dl></section>`;
}

function summaryRow(label, value) {
  return `<div><dt>${escapeHtml(label)}</dt><dd>${escapeHtml(value ?? "-")}</dd></div>`;
}

function detailRow(label, value) {
  return `<div><dt>${escapeHtml(label)}</dt><dd>${escapeHtml(value ?? "-")}</dd></div>`;
}

function startUtcClock() {
  const clock = document.querySelector("#utcClock");
  function tick() {
    clock.textContent = new Date().toISOString().replace("T", " ").slice(0, 19) + " UTC";
  }
  tick();
  setInterval(tick, 1000);
}

function money(value) {
  return Number(value || 0).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function statusClass(status) {
  const s = String(status || "");
  if (s === "AVAILABLE" || s === "PARKED") return "good";
  if (s === "IN_FLIGHT") return "warn";
  if (s === "MAINTENANCE") return "bad";
  return "";
}

function conditionClass(value) {
  const n = Number(value || 0);
  if (n <= 45) return "condition-bad";
  if (n <= 70) return "condition-warn";
  return "condition-ok";
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&","&amp;")
    .replaceAll("<","&lt;")
    .replaceAll(">","&gt;")
    .replaceAll('"',"&quot;")
    .replaceAll("'","&#039;");
}
