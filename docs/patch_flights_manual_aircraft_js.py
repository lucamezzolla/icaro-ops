#!/usr/bin/env python3
from pathlib import Path

path = Path("src/js/routes.js")
text = path.read_text(encoding="utf-8")

# Add endpoint.
text = text.replace(
    'aircraftByIcao: code => `api/public/fleet/model-by-icao.php?icao=${encodeURIComponent(code)}`',
    'aircraftByIcao: code => `api/public/fleet/model-by-icao.php?icao=${encodeURIComponent(code)}`,\n  ownedAircraftModels: "api/public/fleet/owned-models.php"'
)

# Avoid duplicate if script is run twice.
text = text.replace('ownedAircraftModels: "api/public/fleet/owned-models.php",\n  ownedAircraftModels: "api/public/fleet/owned-models.php"', 'ownedAircraftModels: "api/public/fleet/owned-models.php"')

# Load owned models when opening dialog.
text = text.replace(
    "setupFlightTypeToggle();\n  setupFlightTypeExplanation();\n  applyFlightTypeState();\n\n  dialog.showModal();",
    "setupFlightTypeToggle();\n  setupFlightTypeExplanation();\n  applyFlightTypeState();\n  loadOwnedAircraftModelsForFlight();\n\n  dialog.showModal();"
)

# Add selected models to payload.
text = text.replace(
    'route_category_code: document.querySelector("#routeCategory")?.value || "",\n    origin_airport_icao_code:',
    'route_category_code: document.querySelector("#routeCategory")?.value || "",\n    selected_aircraft_model_codes: selectedAircraftModelCodes(),\n    origin_airport_icao_code:'
)

helpers = r'''
async function loadOwnedAircraftModelsForFlight() {
  const container = document.querySelector("#ownedAircraftModelChoices");

  if (!container) {
    return;
  }

  container.innerHTML = `<p class="muted">Loading owned airplanes...</p>`;

  try {
    const data = await getJson(API.ownedAircraftModels);
    const models = data.models || [];

    if (!models.length) {
      container.innerHTML = `<p class="muted">No owned airplanes yet. Buy an aircraft from Fleet first.</p>`;
      return;
    }

    container.innerHTML = models.map(model => `
      <label class="choice-row">
        <input
          type="checkbox"
          name="selected_aircraft_model_codes"
          value="${escapeHtml(model.model_code)}"
          ${models.length === 1 ? "checked" : ""}
        >
        <span>
          <strong>${escapeHtml(model.icao_type_code || model.model_code)}</strong>
          ${escapeHtml(model.manufacturer || "")} ${escapeHtml(model.model_name || "")}
          <small class="muted">
            Owned: ${escapeHtml(model.owned_count || 0)}
            · Available: ${escapeHtml(model.available_count || 0)}
            · Registrations: ${escapeHtml(model.registrations || "-")}
          </small>
        </span>
      </label>
    `).join("");
  } catch (error) {
    container.innerHTML = `<p class="page-error">${escapeHtml(error.message || "Unable to load owned airplanes.")}</p>`;
  }
}

function selectedAircraftModelCodes() {
  return Array.from(document.querySelectorAll("input[name='selected_aircraft_model_codes']:checked"))
    .map(input => input.value)
    .filter(Boolean);
}
'''

if "function loadOwnedAircraftModelsForFlight()" not in text:
    marker = "function flightFormPayload()"
    pos = text.find(marker)
    if pos != -1:
        text = text[:pos] + helpers + "\n\n" + text[pos:]
    else:
        text += "\n" + helpers + "\n"

path.write_text(text, encoding="utf-8")
print("OK: routes.js now loads manually selected owned airplane models.")
