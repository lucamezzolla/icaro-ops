const API = {
  fleet: "api/public/fleet/my-aircraft.php",
  catalog: "api/public/fleet/catalog.php",
  detail: id => `api/public/fleet/detail.php?aircraftId=${encodeURIComponent(id)}`,
  buyNew: "api/public/fleet/buy-new.php",
  modelDetail: id => `api/public/fleet/model-detail.php?modelId=${encodeURIComponent(id)}`
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
    list.innerHTML = `<p class="muted">No aircraft available for your current level.</p>`;
    return;
  }

  list.innerHTML = `
    <div class="info-box">
      <strong>Development open aircraft market</strong>
      <p>
        All aircraft models are visible for testing. Purchase is limited only by company budget.
      </p>
      <p>
        Pilot qualifications, base level, reputation, endgame locks and progression rules are disabled in this development market.
      </p>
    </div>

    <div class="table-wrap catalog-table-wrap">
      <table>
        <thead>
          <tr>
            <th>Aircraft</th>
            <th>ICAO</th>
            <th>Capacity</th>
            <th>Range</th>
            <th>Cruise</th>
            <th>Price</th>
            <th>Buy rule</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          ${rows.map(a => `
            <tr>
              <td><strong>${escapeHtml(a.manufacturer)} ${escapeHtml(a.model_name)}</strong></td>
              <td>${escapeHtml(a.icao_type_code || "-")}</td>
              <td>${escapeHtml(a.passenger_capacity_standard ?? "-")}</td>
              <td>${escapeHtml(a.range_km ?? "-")} km</td>
              <td>${escapeHtml(a.cruise_speed_kmh ?? "-")} km/h</td>
              <td>${money(a.new_purchase_price || 0)} ${escapeHtml(a.currency_code || "EUR")}</td>
              <td>
                <span class="badge ${a.can_afford === false ? "warn" : "good"}">
                  ${a.can_afford === false ? "Need budget" : "Budget only"}
                </span>
              </td>
              <td>
                <div class="button-row">
                  <button type="button" data-model-detail="${a.aircraft_model_id || a.id}">Details</button>
                  <button type="button" data-buy-model="${a.aircraft_model_id || a.id}" class="secondary">Buy</button>
                </div>
              </td>
            </tr>
          `).join("")}
        </tbody>
      </table>
    </div>
  `;

  list.querySelectorAll("[data-buy-model]").forEach(button => {
    button.addEventListener("click", () => buyAircraft(Number(button.dataset.buyModel)));
  });

  list.querySelectorAll("[data-model-detail]").forEach(button => {
    button.addEventListener("click", () => openCatalogModelDetail(Number(button.dataset.modelDetail)));
  });
}




async function openCatalogModelDetail(modelId) {
  const detailDialog = document.querySelector("#aircraftDetailDialog");
  const title = document.querySelector("#aircraftDetailTitle");
  const content = document.querySelector("#aircraftDetailContent");

  title.textContent = "Aircraft model";
  content.textContent = "Loading...";
  detailDialog.showModal();

  try {
    const data = await getJson(API.modelDetail(modelId));
    const m = data.model;

    title.textContent = `${m.manufacturer} ${m.model_name}`;

    content.innerHTML = `
      <div class="model-image-wrap">
        ${m.image_asset_path ? `<img src="${escapeHtml(m.image_asset_path)}" alt="${escapeHtml(m.manufacturer)} ${escapeHtml(m.model_name)}">` : `<p class="muted">No image available.</p>`}
      </div>

      <div class="detail-grid">
        ${section("Identity", [
          ["Manufacturer", m.manufacturer],
          ["Model", m.model_name],
          ["Model code", m.model_code],
          ["ICAO type", m.icao_type_code],
          ["Operation role", m.operation_role],
          ["Unlock", m.unlock_note]
        ])}
        ${section("Capacity", [
          ["Passengers", m.passenger_capacity_standard],
          ["Cargo", `${m.cargo_capacity_kg ?? "-"} kg`],
          ["Crew required", m.crew_required ?? "-"]
        ])}
        ${section("Performance", [
          ["Range", `${m.range_km ?? "-"} km`],
          ["Cruise speed", `${m.cruise_speed_kmh ?? "-"} km/h`],
          ["Fuel burn", `${m.fuel_burn_kg_per_hour ?? "-"} kg/h`],
          ["Runway requirement", `${m.runway_requirement_m ?? "-"} m`],
          ["Service ceiling", `${m.service_ceiling_ft ?? "-"} ft`],
          ["Engine type", m.engine_type ?? "-"]
        ])}
        ${section("Economics", [
          ["New price", `${money(m.new_purchase_price || 0)} ${m.currency_code || "EUR"}`],
          ["Maintenance cost/h", `${money(m.maintenance_cost_per_hour || 0)} ${m.currency_code || "EUR"}`]
        ])}
      </div>

      <div class="dialog-action-bar">
        <button type="button" ${m.is_available_for_current_level ? "" : "disabled"} id="buyModelFromDetailButton">
          Buy this aircraft
        </button>
      </div>
    `;

    const buyButton = content.querySelector("#buyModelFromDetailButton");
    if (buyButton && m.is_available_for_current_level) {
      buyButton.addEventListener("click", async () => {
        await buyAircraft(Number(m.aircraft_model_id || m.id));
        detailDialog.close();
      });
    }
  } catch (error) {
    content.innerHTML = `<div class="page-error">${escapeHtml(error.message || "Unable to load aircraft model detail.")}</div>`;
  }
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

    if (code === "INSUFFICIENT_FUNDS") {
      lines.push(body?.message || "Company budget is not enough to buy this aircraft.");

      if (body?.missing_amount !== undefined) {
        lines.push(`Missing amount: ${body.missing_amount}`);
      }
    } else {
      lines.push(body?.message || code || `Request failed: ${response.status}`);
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
