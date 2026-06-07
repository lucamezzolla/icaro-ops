#!/usr/bin/env python3
from pathlib import Path

fleet_js = Path('src/js/fleet.js')
if not fleet_js.exists():
    raise SystemExit('src/js/fleet.js not found. Run this script from the icaro-ops project root.')

text = fleet_js.read_text()
original = text

# The delivery airport dialog must be a simple ICAO input, not a search UI.
# Remove the airport search endpoint if a previous patch added it.
text = text.replace(
    '  modelDetail: id => `api/public/fleet/model-detail.php?modelId=${encodeURIComponent(id)}`,'
    '\n  airports: q => `api/public/airports/search.php?q=${encodeURIComponent(q || "")}&limit=30`',
    '  modelDetail: id => `api/public/fleet/model-detail.php?modelId=${encodeURIComponent(id)}`'
)
text = text.replace(
    '  modelDetail: id => `api/public/fleet/model-detail.php?modelId=${encodeURIComponent(id)}`,'
    '\n  airports: q => `api/public/airports/search.php?q=${encodeURIComponent(q || "")}&limit=30`\n',
    '  modelDetail: id => `api/public/fleet/model-detail.php?modelId=${encodeURIComponent(id)}`\n'
)

new_choose = '''function chooseDeliveryAirport() {
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
'''

start = text.find('function chooseDeliveryAirport()')
if start == -1:
    raise SystemExit('function chooseDeliveryAirport() was not found in src/js/fleet.js. Apply the delivery dialog patch first, then run this patch.')

# Replace chooseDeliveryAirport and remove the debounce helper if it was only used by airport search.
end = text.find('\nfunction debounce(', start)
if end != -1:
    get_json_start = text.find('\nasync function getJson', end)
    if get_json_start == -1:
        raise SystemExit('Unable to find async function getJson after debounce helper in src/js/fleet.js.')
    text = text[:start] + new_choose + text[get_json_start:]
else:
    get_json_start = text.find('\nasync function getJson', start)
    if get_json_start == -1:
        raise SystemExit('Unable to find async function getJson after chooseDeliveryAirport in src/js/fleet.js.')
    text = text[:start] + new_choose + text[get_json_start:]

if text == original:
    print('No changes were needed in src/js/fleet.js.')
else:
    fleet_js.write_text(text)
    print('Patched src/js/fleet.js: delivery airport dialog now asks for a simple ICAO code only.')
