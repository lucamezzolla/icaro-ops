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
      renderAircraftTable(body, aircraft);
    } catch (error) {
      body.innerHTML = `<div class="page-error">${escapeHtml(error.message || "Unable to load aircraft market.")}</div>`;
    }
  }

  function renderAircraftTable(container, aircraft) {
    if (!aircraft.length) {
      container.innerHTML = `<p class="muted">No aircraft models found.</p>`;
      return;
    }

    container.innerHTML = `
      <table class="compact-dialog-table">
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
        <tbody>
          ${aircraft.map(row => `
            <tr>
              <td><strong>${escapeHtml(row.icao_type_code || row.model_code)}</strong></td>
              <td>${escapeHtml(row.manufacturer || "")} ${escapeHtml(row.model_name || "")}</td>
              <td>${escapeHtml(row.passenger_capacity_standard ?? "-")}</td>
              <td>${escapeHtml(row.range_km ?? "-")} km</td>
              <td>${money(row.new_purchase_price)} ${escapeHtml(row.currency_code || "")}</td>
              <td>
                <button type="button" data-aircraft-detail="${row.aircraft_model_id || row.id}">Details</button>
                <button type="button" data-aircraft-buy="${row.aircraft_model_id || row.id}" class="primary">Buy</button>
              </td>
            </tr>
          `).join("")}
        </tbody>
      </table>
    `;

    container.querySelectorAll("[data-aircraft-detail]").forEach(button => {
      button.addEventListener("click", () => showAircraftDetail(Number(button.dataset.aircraftDetail)));
    });

    container.querySelectorAll("[data-aircraft-buy]").forEach(button => {
      button.addEventListener("click", () => buyAircraft(Number(button.dataset.aircraftBuy)));
    });
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
              <tr>
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

  function escapeHtml(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }
})();
