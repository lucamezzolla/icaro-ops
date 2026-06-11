#!/usr/bin/env python3
from pathlib import Path

PROJECT = Path.cwd()
ROUTES_JS = PROJECT / "src/js/routes.js"
ROUTES_CSS = PROJECT / "src/css/routes.css"

START_FLIGHT_NOW = 'async function startFlightNow(serviceId) {\n  hideError();\n\n  try {\n    const data = await getJson(API.availableAircraft(serviceId));\n    const available = data.available_aircraft || [];\n\n    if (!available.length) {\n      showError("This flight cannot depart: no compatible available aircraft is present at the origin airport.");\n      return;\n    }\n\n    let aircraftId = null;\n\n    if (available.length === 1) {\n      aircraftId = Number(available[0].company_aircraft_id || available[0].aircraft_id);\n    } else {\n      aircraftId = await chooseAircraftForOnDemandFlight(data.flight, available);\n    }\n\n    if (!aircraftId) {\n      return;\n    }\n\n    const result = await postJson(API.startServiceFlight, {\n      service_id: serviceId,\n      company_aircraft_id: aircraftId\n    });\n\n    await showStartedFlightDialog(result);\n    await loadFlights();\n  } catch (error) {\n    showError(error.message || "Unable to start flight.");\n  }\n}'
CHOOSE_DIALOG = 'function chooseAircraftForOnDemandFlight(flight, aircraft) {\n  return new Promise(resolve => {\n    const dialog = document.createElement("dialog");\n    dialog.id = "chooseAircraftDialog";\n    dialog.innerHTML = `\n      <form method="dialog" class="dialog-card">\n        <header class="dialog-header">\n          <div>\n            <p class="eyebrow">Manual dispatch</p>\n            <h2>Choose aircraft</h2>\n          </div>\n          <button type="button" class="close-button" aria-label="Close">×</button>\n        </header>\n\n        <div class="dialog-body">\n          <section class="dispatch-summary-card">\n            <h3>Non-scheduled flight</h3>\n            <dl class="detail-list">\n              ${detailRow("Flight", flight.flight_code || "-")}\n              ${detailRow("Type", flight.service_type || "ON_DEMAND")}\n              ${detailRow("Route", `${flight.origin_airport_icao_code || "-"} → ${flight.destination_airport_icao_code || "-"}`)}\n              ${detailRow("Compatible ICAO types", flight.compatible_aircraft_icao_codes || "-")}\n              ${detailRow("Configured aircraft models", flight.compatible_aircraft_model_codes || "-")}\n            </dl>\n            <p class="muted">\n              This is a non-scheduled flight. Choose one of the compatible available aircraft configured when the flight was created.\n            </p>\n          </section>\n\n          <section class="detail-section">\n            <h3>Available aircraft at ${escapeHtml(flight.origin_airport_icao_code || "-")}</h3>\n            <div class="aircraft-choice-list">\n              ${aircraft.map((a, index) => `\n                <label class="aircraft-choice-row">\n                  <input type="radio" name="dispatch_aircraft" value="${escapeHtml(a.company_aircraft_id || a.aircraft_id)}" ${index === 0 ? "checked" : ""}>\n                  <span>\n                    <strong>${escapeHtml(a.registration_code)} · ${escapeHtml(a.icao_type_code || a.model_code)}</strong>\n                    ${escapeHtml(a.manufacturer || "")} ${escapeHtml(a.model_name || "")}\n                    <small class="muted">\n                      Condition ${escapeHtml(a.condition_percent ?? "-")}%\n                      · Estimated score ${money(a.estimated_profit_score || 0)}\n                    </small>\n                  </span>\n                </label>\n              `).join("")}\n            </div>\n          </section>\n        </div>\n\n        <footer class="dialog-footer">\n          <button type="button" id="cancelAircraftChoice">Cancel</button>\n          <button type="button" id="confirmAircraftChoice" class="primary">Start flight</button>\n        </footer>\n      </form>\n    `;\n\n    document.body.appendChild(dialog);\n\n    const close = value => {\n      dialog.close();\n      dialog.remove();\n      resolve(value);\n    };\n\n    dialog.querySelector(".close-button").addEventListener("click", () => close(null));\n    dialog.querySelector("#cancelAircraftChoice").addEventListener("click", () => close(null));\n    dialog.querySelector("#confirmAircraftChoice").addEventListener("click", () => {\n      const selected = dialog.querySelector("input[name=\'dispatch_aircraft\']:checked");\n      close(selected ? Number(selected.value) : null);\n    });\n\n    dialog.showModal();\n  });\n}'
STARTED_DIALOG = 'function showStartedFlightDialog(result) {\n  return new Promise(resolve => {\n    const dialog = document.createElement("dialog");\n    dialog.id = "startedFlightDialog";\n    dialog.innerHTML = `\n      <form method="dialog" class="dialog-card">\n        <header class="dialog-header">\n          <div>\n            <p class="eyebrow">Flight started</p>\n            <h2>${escapeHtml(result.flight_code || "Flight")}</h2>\n          </div>\n          <button type="button" class="close-button" aria-label="Close">×</button>\n        </header>\n\n        <div class="dialog-body">\n          <section class="dispatch-summary-card">\n            <h3>Dispatch summary</h3>\n            <dl class="detail-list">\n              ${detailRow("Status", result.status || "IN_FLIGHT")}\n              ${detailRow("Flight code", result.flight_code || "-")}\n              ${detailRow("Aircraft", `${result.aircraft?.registration_code || "-"} · ${result.aircraft?.icao_type_code || result.aircraft?.model_code || "-"}`)}\n              ${detailRow("Crew", `${result.crew?.pilot_1 || "-"} / ${result.crew?.pilot_2 || "-"}`)}\n              ${detailRow("Technician", result.crew?.technician || "-")}\n              ${detailRow("Estimated profit", `${money(result.estimated_profit || 0)} ${result.currency_code || "EUR"}`)}\n              ${detailRow("Scheduled arrival UTC", result.scheduled_arrival_at_utc || "-")}\n            </dl>\n          </section>\n        </div>\n\n        <footer class="dialog-footer">\n          <button type="button" id="closeStartedFlightDialog" class="primary">Close</button>\n        </footer>\n      </form>\n    `;\n\n    document.body.appendChild(dialog);\n\n    const close = () => {\n      dialog.close();\n      dialog.remove();\n      resolve();\n    };\n\n    dialog.querySelector(".close-button").addEventListener("click", close);\n    dialog.querySelector("#closeStartedFlightDialog").addEventListener("click", close);\n    dialog.showModal();\n  });\n}'
CSS_APPEND = '\n.dispatch-summary-card {\n  margin: 0 0 14px;\n  padding: 14px;\n  border: 1px solid rgba(255,255,255,.12);\n  border-radius: 16px;\n  background: rgba(255,255,255,.05);\n}\n\n.dispatch-summary-card h3 {\n  margin-top: 0;\n}\n\n.aircraft-choice-list {\n  display: grid;\n  gap: 10px;\n}\n\n.aircraft-choice-row {\n  display: grid;\n  grid-template-columns: auto 1fr;\n  gap: 10px;\n  align-items: start;\n  padding: 12px;\n  border: 1px solid rgba(255,255,255,.12);\n  border-radius: 14px;\n  background: rgba(255,255,255,.04);\n  cursor: pointer;\n}\n\n.aircraft-choice-row:hover {\n  border-color: rgba(115,215,255,.55);\n}\n\n.aircraft-choice-row small {\n  display: block;\n  margin-top: 4px;\n}\n'

def read(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path}")
    return path.read_text(encoding="utf-8")

def write(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")

def replace_function(content: str, function_name: str, new_function: str) -> str:
    marker = "function " + function_name + "("
    async_marker = "async function " + function_name + "("

    start = content.find(async_marker)
    if start < 0:
        start = content.find(marker)
    if start < 0:
        raise RuntimeError(f"Function not found: {function_name}")

    brace = content.find("{", start)
    if brace < 0:
        raise RuntimeError(f"Opening brace not found for: {function_name}")

    depth = 0
    i = brace
    in_string = None
    escape = False
    in_line_comment = False
    in_block_comment = False
    template_depth = 0

    while i < len(content):
        ch = content[i]
        nxt = content[i + 1] if i + 1 < len(content) else ""

        if in_line_comment:
            if ch == "\n":
                in_line_comment = False
            i += 1
            continue

        if in_block_comment:
            if ch == "*" and nxt == "/":
                in_block_comment = False
                i += 2
                continue
            i += 1
            continue

        if in_string:
            if escape:
                escape = False
                i += 1
                continue
            if ch == "\\":
                escape = True
                i += 1
                continue
            if in_string == "`":
                if ch == "$" and nxt == "{":
                    template_depth += 1
                    i += 2
                    continue
                if ch == "}" and template_depth > 0:
                    template_depth -= 1
                    i += 1
                    continue
                if ch == "`" and template_depth == 0:
                    in_string = None
                    i += 1
                    continue
            elif ch == in_string:
                in_string = None
                i += 1
                continue
            i += 1
            continue

        if ch == "/" and nxt == "/":
            in_line_comment = True
            i += 2
            continue
        if ch == "/" and nxt == "*":
            in_block_comment = True
            i += 2
            continue
        if ch in ("'", '"', "`"):
            in_string = ch
            i += 1
            continue

        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return content[:start] + new_function.rstrip() + content[i + 1:]

        i += 1

    raise RuntimeError(f"Could not find end of function: {function_name}")

def patch_routes_js() -> None:
    js = read(ROUTES_JS)

    js = replace_function(js, "startFlightNow", START_FLIGHT_NOW)
    js = replace_function(js, "chooseAircraftForOnDemandFlight", CHOOSE_DIALOG)

    if "function showStartedFlightDialog(" not in js:
        marker = "\nfunction chooseAircraftForOnDemandFlight("
        if marker not in js:
            raise RuntimeError("Could not find chooseAircraftForOnDemandFlight marker after patch.")
        js = js.replace(marker, "\n" + STARTED_DIALOG.rstrip() + "\n" + marker, 1)

    write(ROUTES_JS, js)

def patch_routes_css() -> None:
    css = read(ROUTES_CSS)

    if "dispatch-summary-card" not in css:
        css = css.rstrip() + "\n\n" + CSS_APPEND.strip() + "\n"

    write(ROUTES_CSS, css)

def main() -> None:
    patch_routes_js()
    patch_routes_css()
    print("Patched on-demand manual dispatch: aircraft choice and start result now use dialogs instead of popup alerts.")

if __name__ == "__main__":
    main()
