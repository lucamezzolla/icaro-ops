#!/usr/bin/env python3
from pathlib import Path

fleet_js = Path('src/js/fleet.js')
if not fleet_js.exists():
    raise SystemExit('src/js/fleet.js not found. Run this script from the icaro-ops project root.')

text = fleet_js.read_text()
original = text

# 1) Add airports search endpoint to the Fleet page API map.
if 'airports: q =>' not in text:
    old = '  modelDetail: id => `api/public/fleet/model-detail.php?modelId=${encodeURIComponent(id)}`\n};'
    new = '  modelDetail: id => `api/public/fleet/model-detail.php?modelId=${encodeURIComponent(id)}`,\n  airports: q => `api/public/airports/search.php?q=${encodeURIComponent(q || "")}&limit=30`\n};'
    if old not in text:
        raise SystemExit('Unable to patch API map in src/js/fleet.js. Expected modelDetail entry was not found.')
    text = text.replace(old, new)

# 2) Close the aircraft detail dialog only after a successful purchase.
old_detail_listener = '''    const buyButton = content.querySelector("#buyModelFromDetailButton");
    if (buyButton && m.is_available_for_current_level) {
      buyButton.addEventListener("click", async () => {
        await buyAircraft(Number(m.aircraft_model_id || m.id));
        detailDialog.close();
      });
    }
'''
new_detail_listener = '''    const buyButton = content.querySelector("#buyModelFromDetailButton");
    if (buyButton && m.is_available_for_current_level) {
      buyButton.addEventListener("click", async () => {
        const purchased = await buyAircraft(Number(m.aircraft_model_id || m.id));

        if (purchased) {
          detailDialog.close();
        }
      });
    }
'''
if old_detail_listener in text:
    text = text.replace(old_detail_listener, new_detail_listener)

# 3) Replace old buyAircraft implementation with delivery-airport flow.
old_buy = '''async function buyAircraft(aircraftModelId) {
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
'''
new_buy = '''async function buyAircraft(aircraftModelId) {
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
      <form method="dialog" class="dialog-card delivery-airport-dialog-card">
        <header class="dialog-header">
          <div>
            <p class="eyebrow">Aircraft delivery</p>
            <h2>Choose delivery airport</h2>
          </div>
          <button type="button" class="close-button" aria-label="Close">×</button>
        </header>

        <div class="dialog-body">
          <p class="muted">
            The aircraft will be delivered as available at the selected airport.
            This is the airport from which it can operate its first flight.
          </p>

          <label>
            Delivery airport
            <input id="fleetDeliveryAirportSearch" type="text" placeholder="ICAO, IATA, city or airport name" autocomplete="off">
          </label>

          <div id="fleetDeliveryAirportResults" class="delivery-airport-results">
            <p class="muted">Type at least one character, for example LIRA, LEBL, Rome or Barcelona.</p>
          </div>
        </div>

        <footer class="dialog-footer">
          <button type="button" id="cancelFleetDeliveryAirport">Cancel</button>
        </footer>
      </form>
    `;

    document.body.appendChild(dialog);

    const input = dialog.querySelector("#fleetDeliveryAirportSearch");
    const results = dialog.querySelector("#fleetDeliveryAirportResults");

    const close = value => {
      dialog.close();
      dialog.remove();
      resolve(value);
    };

    const renderAirports = airports => {
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

    const loadAirports = debounce(async () => {
      const q = input.value.trim();

      if (!q) {
        results.innerHTML = `<p class="muted">Type at least one character, for example LIRA, LEBL, Rome or Barcelona.</p>`;
        return;
      }

      results.innerHTML = `<p class="muted">Searching...</p>`;

      try {
        const data = await getJson(API.airports(q));
        renderAirports(data.airports || []);
      } catch (error) {
        results.innerHTML = `<div class="page-error">${escapeHtml(error.message || "Unable to search airports.")}</div>`;
      }
    }, 250);

    input.addEventListener("input", loadAirports);
    dialog.querySelector(".close-button").addEventListener("click", () => close(null));
    dialog.querySelector("#cancelFleetDeliveryAirport").addEventListener("click", () => close(null));
    dialog.addEventListener("cancel", () => close(null));

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
'''

if 'function chooseDeliveryAirport()' not in text:
    if old_buy not in text:
        raise SystemExit('Unable to patch buyAircraft in src/js/fleet.js. Expected old function was not found.')
    text = text.replace(old_buy, new_buy)
else:
    print('chooseDeliveryAirport already exists; leaving existing implementation in place.')

if text == original:
    print('No changes were needed in src/js/fleet.js.')
else:
    fleet_js.write_text(text)
    print('Patched src/js/fleet.js: delivery airport dialog added to Fleet purchase flow.')
