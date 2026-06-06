#!/usr/bin/env python3
from pathlib import Path

path = Path("src/js/routes.js")
text = path.read_text(encoding="utf-8")

if "availableAircraft:" not in text:
    text = text.replace(
        "aircraftByIcao: code => `api/public/fleet/model-by-icao.php?icao=${encodeURIComponent(code)}`",
        "aircraftByIcao: code => `api/public/fleet/model-by-icao.php?icao=${encodeURIComponent(code)}`,\n  availableAircraft: id => `api/public/flights/available-aircraft.php?service_id=${encodeURIComponent(id)}`"
    )

old = """async function startFlightNow(serviceId) {
  hideError();

  if (!confirm("Create and start a real flight instance now?")) {
    return;
  }

  try {
    const result = await postJson(API.startServiceFlight, { service_id: serviceId });

    alert(
      `Flight ${result.flight_code} is now in flight.\\n` +
      `Aircraft: ${result.aircraft?.registration_code || "-"}\\n` +
      `Crew: ${result.crew?.pilot_1 || "-"} / ${result.crew?.pilot_2 || "-"}\\n` +
      `Estimated profit: ${result.estimated_profit || "0.00"}`
    );

    await loadFlights();
  } catch (error) {
    showError(error.message || "Unable to start flight.");
  }
}"""

new = """async function startFlightNow(serviceId) {
  hideError();

  try {
    const data = await getJson(API.availableAircraft(serviceId));
    const available = data.available_aircraft || [];

    if (!available.length) {
      alert("This flight cannot depart: no compatible available aircraft is present at the origin airport.");
      return;
    }

    const aircraftId = await chooseAircraftForOnDemandFlight(data.flight, available);

    if (!aircraftId) {
      return;
    }

    const result = await postJson(API.startServiceFlight, {
      service_id: serviceId,
      company_aircraft_id: aircraftId
    });

    alert(
      `Flight ${result.flight_code} is now in flight.\\n` +
      `Aircraft: ${result.aircraft?.registration_code || "-"}\\n` +
      `Crew: ${result.crew?.pilot_1 || "-"} / ${result.crew?.pilot_2 || "-"}\\n` +
      `Estimated profit: ${result.estimated_profit || "0.00"}`
    );

    await loadFlights();
  } catch (error) {
    showError(error.message || "Unable to start flight.");
  }
}"""

if old in text:
    text = text.replace(old, new)
else:
    print("WARN: original startFlightNow block not found; manual check may be needed.")

helper = """
function chooseAircraftForOnDemandFlight(flight, aircraft) {
  return new Promise(resolve => {
    const dialog = document.createElement("dialog");
    dialog.id = "chooseAircraftDialog";
    dialog.innerHTML = `
      <form method="dialog" class="dialog-card">
        <header class="dialog-header">
          <div>
            <p class="eyebrow">Manual dispatch</p>
            <h2>Choose aircraft</h2>
          </div>
          <button type="button" class="close-button" aria-label="Close">×</button>
        </header>
        <div class="dialog-body">
          <p class="muted">
            Non-scheduled flights require manual aircraft selection.
            Only compatible available aircraft at ${escapeHtml(flight.origin_airport_icao_code)} are listed.
          </p>
          <div class="aircraft-choice-list">
            ${aircraft.map((a, index) => `
              <label class="aircraft-choice-row">
                <input type="radio" name="dispatch_aircraft" value="${escapeHtml(a.company_aircraft_id || a.aircraft_id)}" ${index === 0 ? "checked" : ""}>
                <span>
                  <strong>${escapeHtml(a.registration_code)} · ${escapeHtml(a.icao_type_code || a.model_code)}</strong>
                  ${escapeHtml(a.manufacturer || "")} ${escapeHtml(a.model_name || "")}
                  <small class="muted">
                    Condition ${escapeHtml(a.condition_percent ?? "-")}%
                    · Estimated score ${money(a.estimated_profit_score || 0)}
                  </small>
                </span>
              </label>
            `).join("")}
          </div>
        </div>
        <footer class="dialog-footer">
          <button type="button" id="cancelAircraftChoice">Cancel</button>
          <button type="button" id="confirmAircraftChoice" class="primary">Start flight</button>
        </footer>
      </form>
    `;
    document.body.appendChild(dialog);
    const close = value => {
      dialog.close();
      dialog.remove();
      resolve(value);
    };
    dialog.querySelector(".close-button").addEventListener("click", () => close(null));
    dialog.querySelector("#cancelAircraftChoice").addEventListener("click", () => close(null));
    dialog.querySelector("#confirmAircraftChoice").addEventListener("click", () => {
      const selected = dialog.querySelector("input[name='dispatch_aircraft']:checked");
      close(selected ? Number(selected.value) : null);
    });
    dialog.showModal();
  });
}
"""

if "function chooseAircraftForOnDemandFlight(" not in text:
    text += "\n" + helper + "\n"

path.write_text(text, encoding="utf-8")
print("OK: routes.js patched for manual on-demand aircraft choice.")
