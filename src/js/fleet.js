const API = {
  currentCompany: companyId => `api/public/company/current.php?companyId=${encodeURIComponent(companyId)}`,
  myAircraft: companyId => `api/public/fleet/my-aircraft.php?companyId=${encodeURIComponent(companyId)}`,
  models: companyId => `api/public/fleet/aircraft-models.php?companyId=${encodeURIComponent(companyId)}`,
  buyNew: "api/public/fleet/buy-new.php",
  usedMarket: companyId => `api/public/fleet/used-market.php?companyId=${encodeURIComponent(companyId)}`,
  listForSale: "api/public/fleet/list-for-sale.php",
  purchaseOffer: "api/public/fleet/purchase-offer.php"
};

const ACTIVE_COMPANY_KEY = "icaro_ops_active_company_id";

let companyId = null;
let company = null;

document.addEventListener("DOMContentLoaded", async () => {
  startUtcClock();
  bindAircraftImageDialog();
  companyId = resolveCompanyId();

  document.querySelector("#refreshButton")?.addEventListener("click", () => loadFleetPage());

  if (!companyId) {
    showError("No active company found. Create a company first, or open the dashboard once from your current session.");
    return;
  }

  await loadFleetPage();
});

async function loadFleetPage() {
  hideError();

  try {
    company = await getJson(API.currentCompany(companyId));
    persistActiveCompany(company.company_id);
    renderCompany(company);
    await Promise.all([
      loadMyAircraft(),
      loadCatalog(),
      loadUsedMarket()
    ]);
  } catch (error) {
    showError(error.message || "Unable to load fleet page.");
  }
}

function persistActiveCompany(companyId) {
  if (!companyId) return;

  sessionStorage.setItem(ACTIVE_COMPANY_KEY, String(companyId));

  const raw = sessionStorage.getItem("icaro_ops_company");
  let payload = {};

  if (raw) {
    try {
      payload = JSON.parse(raw);
    } catch {
      payload = {};
    }
  }

  payload.company_id = Number(companyId);
  sessionStorage.setItem("icaro_ops_company", JSON.stringify(payload));
}

function renderCompany(company) {
  const airport = company.base_airport;

  document.querySelector("#companySummary").innerHTML = `
    ${summaryRow("Owner", company.owner_name)}
    ${summaryRow("Company", company.company_name)}
    ${summaryRow("Budget", `${money(company.budget_amount)} ${company.currency_code}`)}
    ${summaryRow("Base", `${airport.icao_code}${airport.iata_code ? " / " + airport.iata_code : ""}`)}
    ${summaryRow("Airport", airport.airport_name)}
  `;

  document.querySelector("#capacitySummary").innerHTML = `
    ${summaryRow("Aircraft", `${airport.aircraft_owned_count} / ${airport.max_aircraft_managed}`)}
    ${summaryRow("At base", `${airport.aircraft_at_base_count} / ${airport.max_aircraft_on_ground}`)}
    ${summaryRow("In flight", airport.aircraft_in_flight_count)}
    ${summaryRow("Maintenance", airport.aircraft_maintenance_count)}
    ${summaryRow("Free fleet", airport.free_managed_aircraft_slots)}
    ${summaryRow("Free ground", airport.free_ground_aircraft_slots)}
  `;
}

async function loadMyAircraft() {
  const rows = await getJson(API.myAircraft(companyId));
  const shell = document.querySelector("#myAircraftTable");

  if (!rows.length) {
    shell.innerHTML = `<p class="muted">No aircraft yet. Buy a new aircraft or look at the used market.</p>`;
    return;
  }

  shell.innerHTML = `
    <table>
      <thead>
        <tr>
          <th>Aircraft</th>
          <th>Registration</th>
          <th>Status</th>
          <th>Base</th>
          <th>Condition</th>
          <th>Value</th>
          <th>Image</th>
          <th>Sale</th>
        </tr>
      </thead>
      <tbody>
        ${rows.map(row => `
          <tr>
            <td>
              <strong>${escapeHtml(row.manufacturer)} ${escapeHtml(row.model_name)}</strong>
              <span>${escapeHtml(row.model_code)} · ${escapeHtml(row.operation_role)} · ${escapeHtml(row.aircraft_category)}</span>
            </td>
            <td>
              <strong>${escapeHtml(row.registration_code)}</strong>
              <span>${escapeHtml(row.manufacture_year)}</span>
            </td>
            <td><span class="badge">${escapeHtml(row.status)}</span></td>
            <td>
              <strong>${escapeHtml(row.home_base_icao_code)}</strong>
              <span>${escapeHtml(row.current_airport_icao_code)}</span>
            </td>
            <td>${escapeHtml(row.condition_percent)}%</td>
            <td>${money(row.current_market_value)} ${escapeHtml(row.currency_code)}</td>
            <td>${aircraftImageButton(row)}</td>
            <td>
              ${row.is_available_for_sale
                ? `<span class="badge">Listed ${money(row.asking_price)} ${escapeHtml(row.currency_code)}</span>`
                : `<button type="button" data-sale-id="${row.company_aircraft_id}">List for sale</button>`
              }
            </td>
          </tr>
        `).join("")}
      </tbody>
    </table>
  `;

  shell.querySelectorAll("[data-sale-id]").forEach(button => {
    button.addEventListener("click", async () => {
      const aircraftId = button.dataset.saleId;
      const price = prompt("Asking price in company currency:");

      if (!price) return;

      await postJson(API.listForSale, {
        company_aircraft_id: Number(aircraftId),
        company_id: Number(companyId),
        asking_price: Number(price)
      });

      await loadFleetPage();
    });
  });
}

async function loadCatalog() {
  const rows = await getJson(API.models(companyId));
  const list = document.querySelector("#catalogList");

  if (!rows.length) {
    list.innerHTML = `<p class="muted">No aircraft models available.</p>`;
    return;
  }

  list.innerHTML = rows.map(model => `
    <article class="catalog-item">
      ${aircraftThumb(model)}
      <h3>${escapeHtml(model.manufacturer)} ${escapeHtml(model.model_name)}</h3>
      <p>${escapeHtml(model.operation_role)} · ${escapeHtml(model.aircraft_category)}</p>
      <div class="catalog-metrics">
        <div><strong>${escapeHtml(model.passenger_capacity_standard)}</strong><span>Passengers</span></div>
        <div><strong>${escapeHtml(model.cargo_capacity_kg)} kg</strong><span>Cargo</span></div>
        <div><strong>${escapeHtml(model.range_km)} km</strong><span>Range</span></div>
        <div><strong>${escapeHtml(model.required_runway_m)} m</strong><span>Runway</span></div>
      </div>
      <p><strong>${money(model.new_purchase_price)} ${escapeHtml(model.currency_code)}</strong></p>
      <div class="catalog-actions">
        ${aircraftImageButton(model)}
        <button type="button" data-buy-model="${model.aircraft_model_id}" ${model.can_buy ? "" : "disabled"}>
          ${model.can_buy ? "Buy new" : model.block_reason || "Unavailable"}
        </button>
      </div>
    </article>
  `).join("");

  list.querySelectorAll("[data-buy-model]").forEach(button => {
    button.addEventListener("click", async () => {
      const modelId = Number(button.dataset.buyModel);

      if (!confirm("Buy this aircraft new?")) return;

      await postJson(API.buyNew, {
        company_id: Number(companyId),
        aircraft_model_id: modelId
      });

      await loadFleetPage();
    });
  });
}

async function loadUsedMarket() {
  const rows = await getJson(API.usedMarket(companyId));
  const list = document.querySelector("#usedMarketList");

  if (!rows.length) {
    list.innerHTML = `<p class="muted">No used aircraft currently listed by other companies.</p>`;
    return;
  }

  list.innerHTML = rows.map(row => `
    <article class="catalog-item">
      ${aircraftThumb(row)}
      <h3>${escapeHtml(row.manufacturer)} ${escapeHtml(row.model_name)}</h3>
      <p>${escapeHtml(row.registration_code)} · seller: ${escapeHtml(row.seller_company_name)}</p>
      <div class="catalog-metrics">
        <div><strong>${escapeHtml(row.condition_percent)}%</strong><span>Condition</span></div>
        <div><strong>${escapeHtml(row.airframe_hours)}</strong><span>Hours</span></div>
        <div><strong>${money(row.current_market_value)}</strong><span>Market value</span></div>
        <div><strong>${money(row.asking_price)}</strong><span>Asking</span></div>
      </div>
      <div class="catalog-actions">
        ${aircraftImageButton(row)}
        <button type="button" data-offer-aircraft="${row.company_aircraft_id}">Make offer</button>
      </div>
    </article>
  `).join("");

  list.querySelectorAll("[data-offer-aircraft]").forEach(button => {
    button.addEventListener("click", async () => {
      const aircraftId = Number(button.dataset.offerAircraft);
      const amount = prompt("Offer amount:");

      if (!amount) return;

      await postJson(API.purchaseOffer, {
        aircraft_id: aircraftId,
        buyer_company_id: Number(companyId),
        offered_amount: Number(amount),
        currency_code: company.currency_code
      });

      alert("Offer created.");
      await loadUsedMarket();
    });
  });
}

function aircraftThumb(item) {
  if (!item.image_asset_path) return "";

  return `
    <button type="button"
      class="aircraft-thumb"
      data-aircraft-image="${escapeHtml(item.image_asset_path)}"
      data-aircraft-title="${escapeHtml(`${item.manufacturer} ${item.model_name}`)}"
      data-aircraft-code="${escapeHtml(item.model_code)}">
      <img src="${escapeHtml(item.image_asset_path)}" alt="${escapeHtml(`${item.manufacturer} ${item.model_name}`)}">
    </button>
  `;
}

function aircraftImageButton(item) {
  return `
    <button type="button"
      class="secondary aircraft-image-button"
      data-aircraft-image="${escapeHtml(item.image_asset_path || "")}"
      data-aircraft-title="${escapeHtml(`${item.manufacturer} ${item.model_name}`)}"
      data-aircraft-code="${escapeHtml(item.model_code || "")}">
      Image
    </button>
  `;
}

function bindAircraftImageDialog() {
  document.addEventListener("click", event => {
    const button = event.target.closest("[data-aircraft-image]");
    if (button) {
      openAircraftImageDialog(
        button.dataset.aircraftImage,
        button.dataset.aircraftTitle,
        button.dataset.aircraftCode
      );
      return;
    }

    if (
      event.target.matches("#aircraftImageDialogClose") ||
      event.target.matches("#aircraftImageDialogBackdrop")
    ) {
      closeAircraftImageDialog();
    }
  });

  document.addEventListener("keydown", event => {
    if (event.key === "Escape") {
      closeAircraftImageDialog();
    }
  });
}

function openAircraftImageDialog(imagePath, title, code) {
  let dialog = document.querySelector("#aircraftImageDialog");

  if (!dialog) {
    document.body.insertAdjacentHTML("beforeend", `
      <div id="aircraftImageDialog" class="aircraft-image-dialog-shell" hidden>
        <div id="aircraftImageDialogBackdrop" class="aircraft-image-dialog-backdrop"></div>
        <section class="aircraft-image-dialog" role="dialog" aria-modal="true" aria-labelledby="aircraftImageDialogTitle">
          <header>
            <div>
              <h2 id="aircraftImageDialogTitle"></h2>
              <p id="aircraftImageDialogCode"></p>
            </div>
            <button id="aircraftImageDialogClose" type="button" aria-label="Close">×</button>
          </header>
          <div class="aircraft-image-dialog-body">
            <img id="aircraftImageDialogImg" alt="">
          </div>
        </section>
      </div>
    `);
    dialog = document.querySelector("#aircraftImageDialog");
  }

  const img = dialog.querySelector("#aircraftImageDialogImg");
  const titleEl = dialog.querySelector("#aircraftImageDialogTitle");
  const codeEl = dialog.querySelector("#aircraftImageDialogCode");

  titleEl.textContent = title || "Aircraft";
  codeEl.textContent = code || "";
  img.src = imagePath || "";
  img.alt = title || "Aircraft image";

  dialog.hidden = false;
}

function closeAircraftImageDialog() {
  const dialog = document.querySelector("#aircraftImageDialog");
  if (dialog) {
    dialog.hidden = true;
  }
}

function resolveCompanyId() {
  const active = sessionStorage.getItem(ACTIVE_COMPANY_KEY);
  if (active) return active;

  const raw = sessionStorage.getItem("icaro_ops_company");
  if (!raw) return null;

  try {
    const parsed = JSON.parse(raw);
    return parsed.company_id || null;
  } catch {
    return null;
  }
}

async function getJson(url) {
  const response = await fetch(url, {
    headers: { "Accept": "application/json" }
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
