const API = {
  fleet: "api/public/fleet/my-aircraft.php",
  catalog: "api/public/fleet/catalog.php",
  detail: id => `api/public/fleet/detail.php?aircraftId=${encodeURIComponent(id)}`,
  buyNew: "api/public/fleet/buy-new.php",
  modelDetail: id => `api/public/fleet/model-detail.php?modelId=${encodeURIComponent(id)}`
};

let ownedAircraft = [];
let catalogAircraft = [];
let fleetSortState = { key: null, direction: "asc" };

document.addEventListener("DOMContentLoaded", async () => {
  startUtcClock();
  document.querySelector("#refreshButton")?.addEventListener("click", loadFleet);
  document.querySelector("#buyAircraftButton")?.addEventListener("click", openBuyDialog);
  setupFleetTableSorting();
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
  const displayRows = sortedFleetRows(rows);

  if (!displayRows.length) {
    tbody.innerHTML = `<tr><td colspan="6">No owned aircraft yet.</td></tr>`;
    return;
  }

  tbody.innerHTML = displayRows.map(a => {
    const aircraftName = `${a.manufacturer || ""} ${a.model_name || ""}`.trim() || "Aircraft";

    return `
      <tr>
        <td><strong>${escapeHtml(a.registration_code)}</strong></td>
        <td>
          <button type="button" class="aircraft-name-link" data-aircraft-detail="${escapeHtml(a.aircraft_id)}">
            ${escapeHtml(aircraftName)}
          </button>
        </td>
        <td><span class="badge fleet-status-badge ${statusClass(a.status)}">${escapeHtml(displayAircraftStatus(a))}</span></td>
        <td class="${conditionClass(a.condition_percent)}">${escapeHtml(a.condition_percent ?? "-")}%</td>
        <td>${escapeHtml(a.airframe_hours ?? "0")}</td>
        <td>${escapeHtml(a.cycles_count ?? "0")}</td>
      </tr>
    `;
  }).join("");

  tbody.querySelectorAll("[data-aircraft-detail]").forEach(button => {
    button.addEventListener("click", () => openAircraftDetailFromButton(button));
  });
}



async 
function setupFleetTableSorting() {
  const table = document.querySelector("#fleetTableBody")?.closest("table");
  if (!table) return;

  table.querySelectorAll("thead th[data-fleet-sort]").forEach(header => {
    const key = header.dataset.fleetSort;
    header.classList.add("sortable-header");
    header.tabIndex = 0;
    header.title = "Sort table";

    const toggle = () => {
      if (fleetSortState.key === key) {
        fleetSortState.direction = fleetSortState.direction === "asc" ? "desc" : "asc";
      } else {
        fleetSortState.key = key;
        fleetSortState.direction = "asc";
      }

      updateFleetSortHeaders();
      renderFleetTable(ownedAircraft);
    };

    header.addEventListener("click", toggle);
    header.addEventListener("keydown", event => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        toggle();
      }
    });
  });
}

function updateFleetSortHeaders() {
  document.querySelectorAll("#fleetTableBody")
    .forEach(tbody => tbody.closest("table")?.querySelectorAll("thead th[data-fleet-sort]")
      .forEach(header => {
        header.classList.remove("sort-asc", "sort-desc");
        header.removeAttribute("aria-sort");

        if (header.dataset.fleetSort === fleetSortState.key) {
          const isAsc = fleetSortState.direction === "asc";
          header.classList.add(isAsc ? "sort-asc" : "sort-desc");
          header.setAttribute("aria-sort", isAsc ? "ascending" : "descending");
        }
      }));
}

function sortedFleetRows(rows) {
  if (!fleetSortState.key) {
    // Initial order is the backend order: first purchased to last purchased.
    return [...rows];
  }

  const direction = fleetSortState.direction === "desc" ? -1 : 1;
  const key = fleetSortState.key;

  return [...rows].sort((a, b) => direction * compareFleetValues(fleetSortValue(a, key), fleetSortValue(b, key)));
}

function fleetSortValue(row, key) {
  if (key === "aircraft_name") {
    return `${row.manufacturer || ""} ${row.model_name || ""}`.trim();
  }

  if (key === "status_display") {
    return displayAircraftStatus(row);
  }

  if (key === "condition_percent" || key === "airframe_hours" || key === "cycles_count") {
    const value = Number(row[key]);
    return Number.isFinite(value) ? value : -1;
  }

  return row[key] ?? "";
}

function compareFleetValues(left, right) {
  if (typeof left === "number" && typeof right === "number") {
    return left - right;
  }

  return String(left ?? "").localeCompare(String(right ?? ""), undefined, {
    numeric: true,
    sensitivity: "base"
  });
}

function displayAircraftStatus(a) {
  const status = String(a.status || a.aircraft_status || "").toUpperCase();

  if (status === "IN_FLIGHT") {
    return "IN FLIGHT";
  }

  const label = status || "UNKNOWN";
  const airport = currentAircraftLocationCode(a);

  return airport && airport !== "-" ? `${label} (${airport})` : label;
}

function currentAircraftLocationCode(a) {
  return a.current_airport_icao_code ||
    a.current_airport ||
    a.current_airport_code ||
    a.home_base_icao_code ||
    "-";
}

function setAircraftDetailFooter(aircraftId) {
  const footer = document.querySelector("#aircraftDetailDialog .dialog-footer");
  if (!footer) return;

  footer.innerHTML = `
    <div class="dialog-footer-actions">
      <button type="button" class="secondary" data-aircraft-image-footer="${escapeHtml(aircraftId)}">Image</button>
      <button type="button" class="secondary" data-aircraft-maintenance-footer="${escapeHtml(aircraftId)}">Maintenance</button>
    </div>
    <button value="close">Close</button>
  `;

  footer.querySelector("[data-aircraft-image-footer]")?.addEventListener("click", event => {
    openAircraftImage(Number(event.currentTarget.dataset.aircraftImageFooter));
  });

  footer.querySelector("[data-aircraft-maintenance-footer]")?.addEventListener("click", event => {
    const id = Number(event.currentTarget.dataset.aircraftMaintenanceFooter);
    if (Number.isInteger(id) && id > 0) {
      window.location.href = `maintenance.html?aircraftId=${encodeURIComponent(id)}`;
    }
  });
}

function resetAircraftDetailFooter() {
  const footer = document.querySelector("#aircraftDetailDialog .dialog-footer");
  if (!footer) return;
  footer.innerHTML = `<button value="close">Close</button>`;
}

async function openAircraftDetail(aircraftId) {
  const dialog = document.querySelector("#aircraftDetailDialog");
  const title = document.querySelector("#aircraftDetailTitle");
  const content = document.querySelector("#aircraftDetailContent");

  title.textContent = "Aircraft";
  content.textContent = "Loading...";
  setAircraftDetailFooter(aircraftId);
  dialog.showModal();

  try {
    const data = await getJson(API.detail(aircraftId));
    const a = data.aircraft;
    title.textContent = `${a.registration_code} · ${a.manufacturer} ${a.model_name}`;
    setAircraftDetailFooter(a.aircraft_id || aircraftId);
    content.innerHTML = renderAircraftDetail(a, data.recent_flights || []);
  } catch (error) {
    resetAircraftDetailFooter();
    content.innerHTML = `<div class="page-error">${escapeHtml(error.message || "Unable to load aircraft detail.")}</div>`;
  }
}



function renderAircraftDetail(a, recentFlights) {
  return `
    ${aircraftDetailImageBlock(a)}
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

function aircraftDetailImageBlock(a) {
  const path = String(a.image_asset_path || "").trim();

  if (!path) {
    return "";
  }

  const aircraftName = `${a.manufacturer || ""} ${a.model_name || ""}`.trim() || "Aircraft";

  return `
    <div class="model-image-wrap owned-aircraft-image-wrap">
      <img src="${escapeHtml(path)}" alt="${escapeHtml(aircraftName)}">
    </div>
  `;
}

function hasAircraftImage(a) {
  return Boolean(String(a?.image_asset_path || "").trim());
}

function openAircraftImage(aircraftId) {
  const a = ownedAircraft.find(item => Number(item.aircraft_id) === Number(aircraftId));
  if (!a) return;

  const path = String(a.image_asset_path || "").trim();

  if (!path) {
    showFleetError("No image is available for this aircraft model yet.");
    return;
  }

  const dialog = document.querySelector("#aircraftImageDialog");
  document.querySelector("#aircraftImageTitle").textContent = `${a.manufacturer} ${a.model_name}`;
  const img = document.querySelector("#aircraftImagePreview");
  img.src = path;
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
    catalogAircraft = sortAircraftByPurchasePrice(data.aircraft || []);
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
                <div class="button-row">
                  <button type="button" data-model-detail="${resolveAircraftModelId(a) || ""}">Details</button>
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

  resetAircraftDetailFooter();
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
        const purchased = await buyAircraft(Number(m.aircraft_model_id || m.id));

        if (purchased) {
          detailDialog.close();
        }
      });
    }
  } catch (error) {
    content.innerHTML = `<div class="page-error">${escapeHtml(error.message || "Unable to load aircraft model detail.")}</div>`;
  }
}


async function buyAircraft(aircraftModelId) {
  const error = document.querySelector("#buyAircraftError");

  if (error) {
    error.hidden = true;
    error.textContent = "";
  }

  const modelId = Number(aircraftModelId);

  if (!Number.isInteger(modelId) || modelId <= 0) {
    showFleetError("Unable to buy aircraft: invalid aircraft model id.");
    return false;
  }

  const deliveryAirport = await chooseDeliveryAirport();

  if (!deliveryAirport) {
    return false;
  }

  if (!confirm(`Buy this aircraft and deliver it to ${deliveryAirport}?`)) {
    return false;
  }

  try {
    const result = await fleetPostJsonWithVisibleErrors(API.buyNew, {
      aircraft_model_id: modelId,
      delivery_airport_icao_code: deliveryAirport
    }, error);

    closeDialogIfOpen("#buyAircraftDialog");
    closeDialogIfOpen("#aircraftMarketTableDialog");
    closeDialogIfOpen("#aircraftDetailDialog");

    await loadFleet();

    showFleetSuccess(
      `Aircraft purchased: ${result.registration_code || "new aircraft"}. ` +
      `Delivered to ${result.delivery_airport?.icao_code || deliveryAirport}.`
    );

    document.querySelector("#fleetTableBody")?.closest("article")?.scrollIntoView({
      behavior: "smooth",
      block: "start"
    });

    return true;
  } catch (err) {
    if (error) {
      error.hidden = false;
      error.textContent = err.message || "Unable to buy aircraft.";
    } else {
      showFleetError(err.message || "Unable to buy aircraft.");
    }

    return false;
  }
}

function closeDialogIfOpen(selector) {
  const dialog = document.querySelector(selector);

  if (dialog?.open) {
    dialog.close();
  }
}

function chooseDeliveryAirport() {
  return new Promise(resolve => {
    const dialog = document.createElement("dialog");
    dialog.id = "fleetDeliveryAirportDialog";
    dialog.innerHTML = `
      <form method="dialog" class="dialog-card delivery-airport-dialog-card" id="fleetDeliveryAirportForm">
        <header class="dialog-header">
          <div>
            <p class="eyebrow">Aircraft delivery</p>
            <h2>Delivery airport</h2>
          </div>
          <button type="button" class="close-button" aria-label="Close">×</button>
        </header>

        <div class="dialog-body">
          <p class="muted">
            Enter the ICAO code of the airport where the aircraft must be delivered.
            This is the airport from which it can operate its first flight.
          </p>

          <label>
            Delivery airport ICAO code
            <input
              id="fleetDeliveryAirportIcao"
              type="text"
              placeholder="Example: LIRA"
              maxlength="4"
              autocomplete="off"
              autocapitalize="characters"
              spellcheck="false"
            >
          </label>

          <div id="fleetDeliveryAirportError" class="page-error" hidden></div>
        </div>

        <footer class="dialog-footer">
          <button type="button" id="cancelFleetDeliveryAirport">Cancel</button>
          <button type="submit" class="primary-button">Continue</button>
        </footer>
      </form>
    `;

    document.body.appendChild(dialog);

    const form = dialog.querySelector("#fleetDeliveryAirportForm");
    const input = dialog.querySelector("#fleetDeliveryAirportIcao");
    const error = dialog.querySelector("#fleetDeliveryAirportError");

    const close = value => {
      dialog.close();
      dialog.remove();
      resolve(value);
    };

    input.addEventListener("input", () => {
      input.value = input.value.toUpperCase().replace(/[^A-Z]/g, "").slice(0, 4);
      error.hidden = true;
      error.textContent = "";
    });

    form.addEventListener("submit", event => {
      event.preventDefault();

      const icaoCode = input.value.trim().toUpperCase();

      if (!icaoCode) {
        error.hidden = false;
        error.textContent = "Enter the delivery airport ICAO code.";
        input.focus();
        return;
      }

      if (!/^[A-Z]{4}$/.test(icaoCode)) {
        error.hidden = false;
        error.textContent = "Enter a valid 4-letter ICAO airport code, for example LIRA.";
        input.focus();
        return;
      }

      close(icaoCode);
    });

    dialog.querySelector(".close-button").addEventListener("click", () => close(null));
    dialog.querySelector("#cancelFleetDeliveryAirport").addEventListener("click", () => close(null));
    dialog.addEventListener("cancel", () => close(null));

    dialog.showModal();
    input.focus();
  });
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



function displayAircraftStatusWithLocation(a) {
  const rawStatus = String(a.status || a.aircraft_status || "-").toUpperCase();
  const status = rawStatus.replace(/_/g, " ");

  if (rawStatus === "IN_FLIGHT") {
    return "IN FLIGHT";
  }

  const location = aircraftLocationLabel(a);
  if (!location || location === "-") {
    return status;
  }

  return `${status} (${location})`;
}

function aircraftLocationLabel(a) {
  const status = String(a.status || a.aircraft_status || "").toUpperCase();

  if (status === "IN_FLIGHT") {
    return "";
  }

  return a.current_airport_icao_code ||
    a.current_airport ||
    a.current_airport_code ||
    a.home_base_icao_code ||
    "-";
}

function displayAircraftAirport(a) {
  return aircraftLocationLabel(a) || "In flight";
}


function aircraftPurchasePriceValue(row) {
  const candidates = [
    row.new_purchase_price,
    row.base_purchase_price,
    row.purchase_price,
    row.estimated_new_price,
    row.catalog_price,
    row.price_amount,
    row.new_cost_amount,
    row.price
  ];

  for (const value of candidates) {
    const number = Number(value);

    if (Number.isFinite(number) && number > 0) {
      return number;
    }
  }

  return Number.MAX_SAFE_INTEGER;
}

function sortAircraftByPurchasePrice(rows) {
  return [...rows].sort((a, b) => {
    const priceDelta = aircraftPurchasePriceValue(a) - aircraftPurchasePriceValue(b);

    if (priceDelta !== 0) {
      return priceDelta;
    }

    return String(a.icao_type_code || a.model_code || a.model_name || "")
      .localeCompare(String(b.icao_type_code || b.model_code || b.model_name || ""));
  });
}


function resolveAircraftModelId(row) {
  const candidates = [
    row.aircraft_model_id,
    row.aircraftModelId,
    row.model_id,
    row.modelId,
    row.id
  ];

  for (const value of candidates) {
    const number = Number(value);

    if (Number.isInteger(number) && number > 0) {
      return number;
    }
  }

  return null;
}

function removeBuyRuleColumnFromAircraftTables(root = document) {
  root.querySelectorAll("table").forEach(table => {
    const headers = Array.from(table.querySelectorAll("thead th, tr:first-child th"));
    const index = headers.findIndex(header => header.textContent.trim().toUpperCase() === "BUY RULE");

    if (index < 0) {
      return;
    }

    table.querySelectorAll("tr").forEach(row => {
      const cells = Array.from(row.children);

      if (cells[index]) {
        cells[index].remove();
      }
    });
  });
}


function aircraftModelIdFromButton(button) {
  const raw = button.dataset.aircraftDetail || button.dataset.modelDetail || "";
  const id = Number(raw);

  return Number.isInteger(id) && id > 0 ? id : null;
}

function showAircraftDetailFromButton(button) {
  const id = aircraftModelIdFromButton(button);

  if (!id) {
    alert("Aircraft details are not available for this row because the model id is missing.");
    return;
  }

  showAircraftDetail(id);
}

function openAircraftDetailFromButton(button) {
  const id = aircraftModelIdFromButton(button);

  if (!id) {
    alert("Aircraft details are not available for this row because the model id is missing.");
    return;
  }

  openAircraftDetail(id);
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&","&amp;")
    .replaceAll("<","&lt;")
    .replaceAll(">","&gt;")
    .replaceAll('"',"&quot;")
    .replaceAll("'","&#039;");
}
