#!/usr/bin/env python3
from pathlib import Path

path = Path("src/js/fleet.js")
text = path.read_text(encoding="utf-8")

if "modelDetail:" not in text:
    text = text.replace(
        'buyNew: "api/public/fleet/buy-new.php"',
        'buyNew: "api/public/fleet/buy-new.php",\n  modelDetail: id => `api/public/fleet/model-detail.php?modelId=${encodeURIComponent(id)}`'
    )

def replace_function(text, name, body):
    needle = f"function {name}("
    start = text.find(needle)
    if start == -1:
        return text + "\n\n" + body + "\n"

    brace = text.find("{", start)
    if brace == -1:
        raise RuntimeError(f"Could not find opening brace for {name}")

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
        raise RuntimeError(f"Could not parse function {name}")

    return text[:start] + body + text[end:]

render_catalog = '''
function renderCatalog(rows, pilotCoverage) {
  const list = document.querySelector("#aircraftCatalogList");

  if (!rows.length) {
    list.innerHTML = `<p class="muted">No aircraft available for your current level.</p>`;
    return;
  }

  list.innerHTML = `
    <div class="info-box">
      <strong>Current level aircraft market</strong>
      <p>
        This table only shows aircraft available for your current operating level.
        Endgame aircraft such as Concorde stay locked until later progression.
      </p>
      <p>
        Qualified pilots: ${escapeHtml(pilotCoverage.current_qualified_pilots ?? "-")}.
        Required for current fleet: ${escapeHtml(pilotCoverage.required_pilots_for_current_fleet ?? "-")}.
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
            <th>Pilot coverage</th>
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
                <span class="badge ${a.pilot_coverage_ok_after_purchase ? "good" : "warn"}">
                  ${escapeHtml(a.current_qualified_pilots ?? "-")} / ${escapeHtml(a.required_pilots_after_purchase ?? "-")}
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
'''

open_model_detail = '''
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
'''

text = replace_function(text, "renderCatalog", render_catalog)

if "function openCatalogModelDetail" not in text:
    marker = "async function buyAircraft("
    pos = text.find(marker)
    if pos != -1:
        text = text[:pos] + open_model_detail + "\n\n" + text[pos:]
    else:
        text += "\n\n" + open_model_detail + "\n"

path.write_text(text, encoding="utf-8")
print("OK: fleet catalog table and model details patched.")
