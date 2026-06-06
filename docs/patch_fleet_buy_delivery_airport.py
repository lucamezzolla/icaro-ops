#!/usr/bin/env python3
from pathlib import Path

path = Path("src/js/fleet-market-table-dialog.js")

if not path.exists():
    raise SystemExit("src/js/fleet-market-table-dialog.js not found. Apply the market table dialog patch first.")

text = path.read_text(encoding="utf-8")

if "airports: q =>" not in text:
    text = text.replace(
        'modelDetail: id => `api/public/fleet/model-detail.php?id=${encodeURIComponent(id)}`',
        'modelDetail: id => `api/public/fleet/model-detail.php?id=${encodeURIComponent(id)}`,\n    airports: q => `api/public/airports/search.php?q=${encodeURIComponent(q || "")}&limit=30`'
    )

start = text.find("  async function buyAircraft(id) {")
if start == -1:
    raise SystemExit("Could not find buyAircraft function in fleet-market-table-dialog.js")

brace = text.find("{", start)
depth = 0
end = None
for i in range(brace, len(text)):
    if text[i] == "{":
        depth += 1
    elif text[i] == "}":
        depth -= 1
        if depth == 0:
            end = i + 1
            break

if end is None:
    raise SystemExit("Could not parse buyAircraft function body")

new_buy = '''  async function buyAircraft(id) {
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

      alert(`Aircraft purchased: ${result.registration_code}\\nDelivered to: ${result.delivery_airport?.icao_code || deliveryAirport}`);
      window.location.reload();
    } catch (error) {
      alert(error.message || "Unable to buy aircraft.");
    }
  }'''

text = text[:start] + new_buy + text[end:]

helper = r'''
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
'''

if "function chooseDeliveryAirport()" not in text:
    marker = "  function ensureDialog()"
    if marker in text:
        text = text.replace(marker, helper + "\n" + marker, 1)
    else:
        text += "\n" + helper

path.write_text(text, encoding="utf-8")
print("OK: fleet market buy flow now asks delivery airport.")
