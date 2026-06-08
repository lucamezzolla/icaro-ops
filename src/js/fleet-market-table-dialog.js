(() => {
  const API = {
    catalog: "api/public/fleet/catalog.php",
    buyNew: "api/public/fleet/buy-new.php",
    modelDetail: id => `api/public/fleet/model-detail.php?id=${encodeURIComponent(id)}`,
    airports: q => `api/public/airports/search.php?q=${encodeURIComponent(q || "")}&limit=30`
  };

  document.addEventListener("click", event => {
    const target = event.target.closest("button, a");

    if (!target || target.closest("#aircraftMarketTableDialog")) {
      return;
    }

    const label = (target.textContent || "").trim().toLowerCase();

    if (
      label.includes("add airplane") ||
      label.includes("add aircraft") ||
      label.includes("buy new aircraft") ||
      label.includes("aircraft market")
    ) {
      event.preventDefault();
      event.stopPropagation();
      event.stopImmediatePropagation();
      openAircraftMarketDialog();
    }
  }, true);

  async function openAircraftMarketDialog() {
    const dialog = ensureDialog();
    const body = dialog.querySelector("#aircraftMarketTableBody");

    body.innerHTML = `<p class="muted">Loading aircraft market...</p>`;
    dialog.showModal();

    try {
      const data = await getJson(API.catalog);
      const aircraft = data.aircraft || [];
      renderAircraftTable(body, sortAircraftByPurchasePrice(aircraft));
      removeBuyRuleColumnFromAircraftTables(document);
    } catch (error) {
      body.innerHTML = `<div class="page-error">${escapeHtml(error.message || "Unable to load aircraft market.")}</div>`;
    }
  }

  function renderAircraftTable(container, aircraft) {
    const allAircraft = Array.isArray(aircraft) ? aircraft : [];

    container.innerHTML = `
      <section class="aircraft-market-filter-panel" aria-label="Aircraft market filters">
        <div class="aircraft-market-filters">
          <label>
            ICAO
            <input id="aircraftMarketFilterIcao" type="text" placeholder="A320, B738, CONC" autocomplete="off">
          </label>
          <label>
            Search
            <input id="aircraftMarketFilterSearch" type="text" placeholder="manufacturer or model" autocomplete="off">
          </label>
          <label>
            Max price
            <input id="aircraftMarketFilterMaxPrice" type="number" min="0" step="100000" placeholder="Any">
          </label>
          <label>
            Min pax
            <input id="aircraftMarketFilterMinPax" type="number" min="0" step="1" placeholder="Any">
          </label>
          <label>
            Max pax
            <input id="aircraftMarketFilterMaxPax" type="number" min="0" step="1" placeholder="Any">
          </label>
          <label>
            Engine
            <select id="aircraftMarketFilterEngine">
              <option value="">All engines</option>
              <option value="TURBOFAN">Turbofan / jet</option>
              <option value="TURBOPROP">Turboprop</option>
              <option value="PISTON">Piston</option>
              <option value="TURBOSHAFT">Turboshaft / helicopter</option>
              <option value="SUPERSONIC">Supersonic</option>
            </select>
          </label>
          <button id="aircraftMarketFilterClear" type="button" class="secondary">Clear</button>
        </div>
        <p id="aircraftMarketFilterSummary" class="muted aircraft-market-filter-summary"></p>
      </section>
      <table class="compact-dialog-table aircraft-market-table">
        <thead>
          <tr>
            <th>ICAO</th>
            <th>Aircraft</th>
            <th>Passengers</th>
            <th>Range</th>
            <th>Price</th>
            <th></th>
          </tr>
        </thead>
        <tbody id="aircraftMarketRows"></tbody>
      </table>
    `;

    const filterIcao = container.querySelector("#aircraftMarketFilterIcao");
    const filterSearch = container.querySelector("#aircraftMarketFilterSearch");
    const filterMaxPrice = container.querySelector("#aircraftMarketFilterMaxPrice");
    const filterMinPax = container.querySelector("#aircraftMarketFilterMinPax");
    const filterMaxPax = container.querySelector("#aircraftMarketFilterMaxPax");
    const filterEngine = container.querySelector("#aircraftMarketFilterEngine");
    const clearButton = container.querySelector("#aircraftMarketFilterClear");
    const summary = container.querySelector("#aircraftMarketFilterSummary");
    const tbody = container.querySelector("#aircraftMarketRows");

    const normalized = value => String(value ?? "").trim().toUpperCase();
    const numeric = value => {
      const number = Number(value);
      return Number.isFinite(number) ? number : null;
    };

    const rowEngine = row => normalized(row.engine_type || row.engineType || row.engine || row.data_engine_type);
    const rowIcao = row => normalized(row.icao_type_code || row.icao || row.model_code);
    const rowText = row => normalized([
      row.manufacturer,
      row.model_name,
      row.model_code,
      row.icao_type_code,
      row.iata_type_code,
      row.engine_type
    ].filter(Boolean).join(" "));

    const matchesFilters = row => {
      const icao = normalized(filterIcao.value);
      const search = normalized(filterSearch.value);
      const engine = normalized(filterEngine.value);
      const maxPrice = numeric(filterMaxPrice.value);
      const minPax = numeric(filterMinPax.value);
      const maxPax = numeric(filterMaxPax.value);
      const price = numeric(row.new_purchase_price);
      const pax = numeric(row.passenger_capacity_standard ?? row.passenger_capacity_max);

      if (icao && !rowIcao(row).includes(icao)) {
        return false;
      }

      if (search && !rowText(row).includes(search)) {
        return false;
      }

      if (engine && rowEngine(row) !== engine) {
        return false;
      }

      if (maxPrice !== null && price !== null && price > maxPrice) {
        return false;
      }

      if (minPax !== null && pax !== null && pax < minPax) {
        return false;
      }

      if (maxPax !== null && pax !== null && pax > maxPax) {
        return false;
      }

      return true;
    };

    const bindRowButtons = () => {
      tbody.querySelectorAll("[data-aircraft-detail]").forEach(button => {
        button.addEventListener("click", () => showAircraftDetailFromButton(button));
      });

      tbody.querySelectorAll("[data-aircraft-buy]").forEach(button => {
        button.addEventListener("click", () => buyAircraft(Number(button.dataset.aircraftBuy)));
      });
    };

    const renderRows = () => {
      const visibleAircraft = allAircraft.filter(matchesFilters);

      summary.textContent = `${visibleAircraft.length} of ${allAircraft.length} aircraft shown`;

      if (!visibleAircraft.length) {
        tbody.innerHTML = `<tr><td colspan="6">No aircraft match the selected filters.</td></tr>`;
        return;
      }

      tbody.innerHTML = visibleAircraft.map(row => {
        const modelId = resolveAircraftModelId(row) || "";
        const engine = rowEngine(row);
        const icao = row.icao_type_code || row.model_code || "";

        return `
          <tr data-engine-type="${escapeHtml(engine)}" data-aircraft-engine="${escapeHtml(engine)}">
            <td><strong>${escapeHtml(icao)}</strong></td>
            <td>${escapeHtml(row.manufacturer || "")} ${escapeHtml(row.model_name || "")}</td>
            <td>${escapeHtml(row.passenger_capacity_standard ?? row.passenger_capacity_max ?? "-")}</td>
            <td>${escapeHtml(row.range_km ?? "-")} km</td>
            <td>${money(row.new_purchase_price)} ${escapeHtml(row.currency_code || "")}</td>
            <td>
              <button type="button" data-aircraft-detail="${escapeHtml(modelId)}">Details</button>
              <button type="button" data-aircraft-buy="${escapeHtml(row.aircraft_model_id || row.id || "")}" class="primary">Buy</button>
            </td>
          </tr>
        `;
      }).join("");

      bindRowButtons();
    };

    [filterIcao, filterSearch, filterMaxPrice, filterMinPax, filterMaxPax].forEach(input => {
      input.addEventListener("input", renderRows);
    });
    filterEngine.addEventListener("change", renderRows);

    clearButton.addEventListener("click", () => {
      filterIcao.value = "";
      filterSearch.value = "";
      filterMaxPrice.value = "";
      filterMinPax.value = "";
      filterMaxPax.value = "";
      filterEngine.value = "";
      renderRows();
    });

    renderRows();
  }

  async function showAircraftDetail(id) {
    const detail = document.querySelector("#aircraftMarketDetail");
    detail.innerHTML = `<p class="muted">Loading detail...</p>`;

    try {
      const data = await getJson(API.modelDetail(id));
      const model = data.model;

      detail.innerHTML = `
        <section class="detail-section">
          <h3>${escapeHtml(model.icao_type_code || model.model_code)} · ${escapeHtml(model.manufacturer)} ${escapeHtml(model.model_name)}</h3>
          ${model.image_asset_path ? `<img class="dialog-model-image" src="${escapeHtml(model.image_asset_path)}" alt="${escapeHtml(model.model_name)}">` : ""}
          <dl class="detail-list">
            ${detailRow("Internal model code", model.model_code)}
            ${detailRow("Role", model.operation_role)}
            ${detailRow("Engine", model.engine_type)}
            ${detailRow("Passengers", model.passenger_capacity_standard)}
            ${detailRow("Range", `${model.range_km ?? "-"} km`)}
            ${detailRow("Cruise speed", `${model.cruise_speed_kmh ?? "-"} km/h`)}
            ${detailRow("Fuel burn", `${model.fuel_burn_kg_per_hour ?? "-"} kg/h`)}
            ${detailRow("Maintenance cost/h", money(model.maintenance_cost_per_hour))}
            ${detailRow("Price", `${money(model.new_purchase_price)} ${model.currency_code || ""}`)}
          </dl>
        </section>
      `;
    } catch (error) {
      detail.innerHTML = `<div class="page-error">${escapeHtml(error.message || "Unable to load aircraft detail.")}</div>`;
    }
  }

  async function buyAircraft(id) {
    const deliveryAirport = await chooseDeliveryAirport();

    if (!deliveryAirport) {
      return;
    }

    if (!confirm(`Buy this aircraft and deliver it to ${deliveryAirport}? Purchase is limited only by budget.`)) {
      return;
    }

    try {
      const result = await postJson(API.buyNew, {
        aircraft_model_id: id,
        delivery_airport_icao_code: deliveryAirport
      });

      alert(`Aircraft purchased: ${result.registration_code}\nDelivered to: ${result.delivery_airport?.icao_code || deliveryAirport}`);
      window.location.reload();
    } catch (error) {
      alert(error.message || "Unable to buy aircraft.");
    }
  }


  function chooseDeliveryAirport() {
    return new Promise(resolve => {
      const dialog = document.createElement("dialog");
      dialog.id = "deliveryAirportDialog";
      dialog.innerHTML = `
        <form method="dialog" class="dialog-card">
          <header class="dialog-header">
            <div>
              <p class="eyebrow">Aircraft delivery</p>
              <h2>Choose delivery airport</h2>
            </div>
            <button type="button" class="close-button" aria-label="Close">×</button>
          </header>
          <div class="dialog-body">
            <p class="muted">
              The aircraft will be delivered as AVAILABLE at the selected airport.
              For now, this airport becomes both its home base and current airport.
            </p>
            <label>
              Search airport
              <input id="deliveryAirportSearch" type="text" placeholder="ICAO, IATA, city or airport name" autocomplete="off">
            </label>
            <div id="deliveryAirportResults" class="delivery-airport-results">
              <p class="muted">Type at least one character, for example LIRA, LEBL, Rome or Barcelona.</p>
            </div>
          </div>
          <footer class="dialog-footer">
            <button type="button" id="cancelDeliveryAirport">Cancel</button>
          </footer>
        </form>
      `;

      document.body.appendChild(dialog);

      const close = value => {
        dialog.close();
        dialog.remove();
        resolve(value);
      };

      const input = dialog.querySelector("#deliveryAirportSearch");
      const results = dialog.querySelector("#deliveryAirportResults");

      const render = airports => {
        if (!airports.length) {
          results.innerHTML = `<p class="muted">No airports found.</p>`;
          return;
        }

        results.innerHTML = `
          <table class="compact-dialog-table">
            <thead>
              <tr data-engine-type="${escapeHtml(row.engine_type || "")}" data-aircraft-engine="${escapeHtml(row.engine_type || "")}">
                <th>ICAO</th>
                <th>IATA</th>
                <th>Airport</th>
                <th>City</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              ${airports.map(airport => `
                <tr>
                  <td><strong>${escapeHtml(airport.icao_code)}</strong></td>
                  <td>${escapeHtml(airport.iata_code || "-")}</td>
                  <td>${escapeHtml(airport.name || "-")}</td>
                  <td>${escapeHtml(airport.city || "-")}</td>
                  <td><button type="button" data-delivery-airport="${escapeHtml(airport.icao_code)}">Deliver here</button></td>
                </tr>
              `).join("")}
            </tbody>
          </table>
        `;

        results.querySelectorAll("[data-delivery-airport]").forEach(button => {
          button.addEventListener("click", () => close(button.dataset.deliveryAirport));
        });
      };

      const load = debounce(async () => {
        const q = input.value.trim();

        if (!q) {
          results.innerHTML = `<p class="muted">Type at least one character, for example LIRA, LEBL, Rome or Barcelona.</p>`;
          return;
        }

        results.innerHTML = `<p class="muted">Searching...</p>`;

        try {
          const data = await getJson(API.airports(q));
          render(data.airports || []);
        } catch (error) {
          results.innerHTML = `<div class="page-error">${escapeHtml(error.message || "Unable to search airports.")}</div>`;
        }
      }, 250);

      input.addEventListener("input", load);
      dialog.querySelector(".close-button").addEventListener("click", () => close(null));
      dialog.querySelector("#cancelDeliveryAirport").addEventListener("click", () => close(null));

      dialog.showModal();
      input.focus();
    });
  }

  function debounce(callback, waitMs) {
    let timeoutId = null;

    return (...args) => {
      window.clearTimeout(timeoutId);
      timeoutId = window.setTimeout(() => callback(...args), waitMs);
    };
  }

  function ensureDialog() {
    let dialog = document.querySelector("#aircraftMarketTableDialog");

    if (dialog) {
      return dialog;
    }

    dialog = document.createElement("dialog");
    dialog.id = "aircraftMarketTableDialog";
    dialog.innerHTML = `
      <form method="dialog" class="dialog-card wide-dialog">
        <header class="dialog-header">
          <div>
            <p class="eyebrow">Open aircraft market</p>
            <h2>Add airplane</h2>
          </div>
          <button type="button" class="close-button" aria-label="Close">×</button>
        </header>
        <div class="dialog-body">
          <p class="muted">All aircraft are visible. The only purchase blocker is company budget.</p>
          <div id="aircraftMarketTableBody"></div>
          <div id="aircraftMarketDetail" class="dialog-detail-panel"></div>
        </div>
        <footer class="dialog-footer">
          <button value="close">Close</button>
        </footer>
      </form>
    `;

    dialog.querySelector(".close-button").addEventListener("click", () => dialog.close());
    document.body.appendChild(dialog);

    return dialog;
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
      headers: { "Accept": "application/json", "Content-Type": "application/json" },
      credentials: "same-origin",
      body: JSON.stringify(payload)
    });
    const body = await response.json().catch(() => null);
    if (!response.ok) {
      throw new Error(body?.message || body?.error || `Request failed: ${response.status}`);
    }
    return body;
  }

  function detailRow(label, value) {
    return `<div><dt>${escapeHtml(label)}</dt><dd>${escapeHtml(value ?? "-")}</dd></div>`;
  }

  function money(value) {
    return Number(value || 0).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
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
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }
})();
