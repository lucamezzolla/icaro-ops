#!/usr/bin/env python3
from pathlib import Path
import re

path = Path("src/js/routes.js")
text = path.read_text(encoding="utf-8")

# API entries.
if "removeService:" not in text:
    text = text.replace(
        'startServiceFlight: "api/public/flights/start-service-now.php"',
        'startServiceFlight: "api/public/flights/start-service-now.php",\n  removeService: "api/public/routes/delete.php",\n  aircraftByIcao: code => `api/public/fleet/model-by-icao.php?icao=${encodeURIComponent(code)}`'
    )
if "aircraftByIcao:" not in text and "removeService:" in text:
    text = text.replace(
        'removeService: "api/public/routes/delete.php"',
        'removeService: "api/public/routes/delete.php",\n  aircraftByIcao: code => `api/public/fleet/model-by-icao.php?icao=${encodeURIComponent(code)}`'
    )

# Make table row show Scheduled + Airplanes only, no ticket/status.
text = text.replace(
'''      <td>${serviceScheduleLabel(service)}</td>
      <td>${modelCodesLabel(service)}</td>
      <td>${money(service.ticket_price)} ${escapeHtml(service.currency_code || "")}</td>''',
'''      <td>${serviceScheduleLabel(service)}</td>
      <td>${airplanesLinks(service)}</td>'''
)

text = text.replace(
'''      <td>${serviceScheduleLabel(service)}</td>
      <td>${modelCodesLabel(service)}</td>
      <td>${money(service.ticket_price)} ${escapeHtml(service.currency_code || "")}</td>
      <td><span class="badge ${service.status === "ACTIVE" ? "good" : "warn"}">${escapeHtml(service.status || "-")}</span></td>''',
'''      <td>${serviceScheduleLabel(service)}</td>
      <td>${airplanesLinks(service)}</td>'''
)

text = text.replace('colspan="8"', 'colspan="5"').replace('colspan="6"', 'colspan="5"')

# Bind airplane buttons.
if "[data-airplane-icao]" not in text:
    old = '''  tbody.querySelectorAll("[data-start-service]").forEach(button => {
    button.addEventListener("click", () => startServiceFlight(Number(button.dataset.startService)));
  });'''
    new = '''  tbody.querySelectorAll("[data-start-service]").forEach(button => {
    button.addEventListener("click", () => startServiceFlight(Number(button.dataset.startService)));
  });

  tbody.querySelectorAll("[data-airplane-icao]").forEach(button => {
    button.addEventListener("click", () => openAircraftModelDialog(button.dataset.airplaneIcao));
  });'''
    text = text.replace(old, new)

# Replace schedule function.
schedule_fn = '''function serviceScheduleLabel(service) {
  const type = service.service_type || (service.scheduled_departure_time_utc ? "SCHEDULED" : "ON_DEMAND");

  if (type === "ON_DEMAND") {
    return "Not scheduled";
  }

  const raw = service.scheduled_departure_time_utc || "";
  return raw.length >= 5 ? raw.slice(0, 5) : "-";
}'''
text = re.sub(r'function serviceScheduleLabel\(service\)\s*\{.*?\n\}', schedule_fn, text, count=1, flags=re.S)

# Add/replace airplane helpers.
air_helpers = '''function modelCodesLabel(service) {
  return escapeHtml(service.compatible_aircraft_icao_codes || service.icao_type_code || "C208");
}

function airplanesLinks(service) {
  const raw = service.compatible_aircraft_icao_codes || service.icao_type_code || "C208";
  const codes = String(raw).split(",").map(code => code.trim()).filter(Boolean);

  return codes.map(code => `
    <button type="button" class="link-button airplane-code-link" data-airplane-icao="${escapeHtml(code)}">${escapeHtml(code)}</button>
  `).join(" ");
}'''
if "function modelCodesLabel(" in text:
    text = re.sub(r'function modelCodesLabel\(service\)\s*\{.*?\n\}', air_helpers, text, count=1, flags=re.S)
elif "function airplanesLinks(" not in text:
    marker = "function openAddRouteDialog()"
    pos = text.find(marker)
    text = text[:pos] + air_helpers + "\n\n" + text[pos:] if pos != -1 else text + "\n" + air_helpers

# Detail wording.
text = text.replace("Compatible models", "Airplanes")
text = text.replace("Preferred models", "Airplanes")
text = text.replace("Preferred model", "Airplanes")

# Add remove service button inside details.
if 'id="removeServiceButton"' not in text:
    marker = '''      </div>
    `;
  } catch (error) {'''
    replacement = '''      </div>
      <div class="dialog-action-bar">
        <button type="button" class="danger" id="removeServiceButton">Remove service</button>
      </div>
    `;

    const removeButton = content.querySelector("#removeServiceButton");
    if (removeButton) {
      removeButton.addEventListener("click", () => removeService(Number(s.id || s.service_id)));
    }
  } catch (error) {'''
    text = text.replace(marker, replacement, 1)

extra_helpers = '''
async function openAircraftModelDialog(icaoCode) {
  const dialog = document.querySelector("#aircraftModelDialog") || ensureAircraftModelDialog();
  const title = dialog.querySelector("#aircraftModelTitle");
  const content = dialog.querySelector("#aircraftModelContent");

  title.textContent = `Aircraft ${icaoCode}`;
  content.textContent = "Loading...";
  dialog.showModal();

  try {
    const data = await getJson(API.aircraftByIcao(icaoCode));
    const m = data.model;

    title.textContent = `${m.icao_type_code} · ${m.manufacturer} ${m.model_name}`;
    content.innerHTML = `
      <div class="model-image-wrap">
        ${m.image_asset_path ? `<img src="${escapeHtml(m.image_asset_path)}" alt="${escapeHtml(m.manufacturer)} ${escapeHtml(m.model_name)}">` : `<p class="muted">No image available.</p>`}
      </div>
      <div class="detail-grid">
        ${section("Identity", [
          ["ICAO type", m.icao_type_code],
          ["Manufacturer", m.manufacturer],
          ["Model", m.model_name],
          ["Internal model code", m.model_code],
          ["Operation role", m.operation_role]
        ])}
        ${section("Performance", [
          ["Passengers", m.passenger_capacity_standard],
          ["Range", `${m.range_km ?? "-"} km`],
          ["Cruise speed", `${m.cruise_speed_kmh ?? "-"} km/h`],
          ["Fuel burn", `${m.fuel_burn_kg_per_hour ?? "-"} kg/h`],
          ["Maintenance cost/h", `${money(m.maintenance_cost_per_hour || 0)}`]
        ])}
        ${section("Economics", [
          ["Indicative new price", `${money(m.new_purchase_price || 0)}`]
        ])}
      </div>
    `;
  } catch (error) {
    content.innerHTML = `<div class="page-error">${escapeHtml(error.message || "Unable to load aircraft model.")}</div>`;
  }
}

function ensureAircraftModelDialog() {
  const dialog = document.createElement("dialog");
  dialog.id = "aircraftModelDialog";
  dialog.innerHTML = `
    <form method="dialog" class="dialog-card">
      <header class="dialog-header">
        <div>
          <p class="eyebrow">Generic airplane model</p>
          <h2 id="aircraftModelTitle">Aircraft</h2>
        </div>
        <button value="close" class="close-button" aria-label="Close">×</button>
      </header>
      <div id="aircraftModelContent" class="dialog-body">Loading...</div>
      <footer class="dialog-footer">
        <button value="close">Close</button>
      </footer>
    </form>
  `;
  document.body.appendChild(dialog);
  return dialog;
}

async function removeService(serviceId) {
  if (!confirm("Remove this service? Existing completed flight history will remain, but the service will be cancelled.")) {
    return;
  }

  try {
    await postJson(API.removeService, { service_id: serviceId });
    document.querySelector("#routeDetailDialog")?.close();
    await loadRoutes();
  } catch (error) {
    alert(error.message || "Unable to remove service.");
  }
}
'''
if "async function openAircraftModelDialog(" not in text:
    marker = "function setupServiceTypeToggle()"
    pos = text.find(marker)
    text = text[:pos] + extra_helpers + "\n\n" + text[pos:] if pos != -1 else text + "\n" + extra_helpers

path.write_text(text, encoding="utf-8")
print("OK: routes.js patched.")
