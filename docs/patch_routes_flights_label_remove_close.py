#!/usr/bin/env python3
from pathlib import Path
import re

path = Path("src/js/routes.js")
text = path.read_text(encoding="utf-8")

# Wording: Services -> Flights in UI labels generated from JS.
text = text.replace("Scheduled service", "Flight route")
text = text.replace("scheduled service", "flight route")
text = text.replace("Scheduled services", "Flights")
text = text.replace("scheduled services", "flights")
text = text.replace("Service / Air route", "Flight / Air route")
text = text.replace("No scheduled services yet.", "No flights yet.")
text = text.replace("Add scheduled service", "Add flight")

# Add/remove API if missing.
if 'removeService:' not in text:
    text = text.replace(
        'startServiceFlight: "api/public/flights/start-service-now.php"',
        'startServiceFlight: "api/public/flights/start-service-now.php",\n  removeService: "api/public/routes/delete.php"'
    )

# Ensure start button appears only for ON_DEMAND rows.
text = text.replace(
'''          <button type="button" data-service-detail="${service.service_id}">Details</button>
          <button type="button" data-start-service="${service.service_id}" class="secondary">Start flight now</button>''',
'''          <button type="button" data-service-detail="${service.service_id}">Details</button>
          ${isOnDemandService(service) ? `<button type="button" data-start-service="${service.service_id}" class="secondary">Start flight now</button>` : ""}'''
)

# If only detail button is present, add conditional start button after it.
text = text.replace(
'''          <button type="button" data-service-detail="${service.service_id}">Details</button>
        </div>''',
'''          <button type="button" data-service-detail="${service.service_id}">Details</button>
          ${isOnDemandService(service) ? `<button type="button" data-start-service="${service.service_id}" class="secondary">Start flight now</button>` : ""}
        </div>'''
)

# Helper for on-demand.
helper_on_demand = r'''
function isOnDemandService(service) {
  const type = service.service_type || (service.scheduled_departure_time_utc ? "SCHEDULED" : "ON_DEMAND");
  return type === "ON_DEMAND";
}
'''
if "function isOnDemandService(" not in text:
    marker = "function serviceScheduleLabel("
    pos = text.find(marker)
    text = text[:pos] + helper_on_demand + "\n" + text[pos:] if pos != -1 else text + "\n" + helper_on_demand

# Remove must close detail and reload.
if "async function removeService(" in text:
    text = re.sub(
        r'async function removeService\(serviceId\)\s*\{.*?\n\}',
        r'''async function removeService(serviceId) {
  if (!confirm("Remove this flight route? Existing completed flight history will remain, but the flight route will be cancelled.")) {
    return;
  }

  try {
    await postJson(API.removeService, { service_id: serviceId });
    document.querySelector("#routeDetailDialog")?.close();
    await loadRoutes();
  } catch (error) {
    alert(error.message || "Unable to remove flight route.");
  }
}''',
        text,
        count=1,
        flags=re.S
    )

# If remove helper was not there, add it.
if "async function removeService(" not in text:
    remove_helper = r'''
async function removeService(serviceId) {
  if (!confirm("Remove this flight route? Existing completed flight history will remain, but the flight route will be cancelled.")) {
    return;
  }

  try {
    await postJson(API.removeService, { service_id: serviceId });
    document.querySelector("#routeDetailDialog")?.close();
    await loadRoutes();
  } catch (error) {
    alert(error.message || "Unable to remove flight route.");
  }
}
'''
    marker = "async function openRouteDetail("
    pos = text.find(marker)
    text = text[:pos] + remove_helper + "\n" + text[pos:] if pos != -1 else text + "\n" + remove_helper

# Ensure remove button exists in detail.
if 'id="removeServiceButton"' not in text:
    marker = '''      </div>
    `;
  } catch (error) {'''
    replacement = '''      </div>
      <div class="dialog-action-bar">
        <button type="button" class="danger" id="removeServiceButton">Remove flight route</button>
      </div>
    `;

    const removeButton = content.querySelector("#removeServiceButton");
    if (removeButton) {
      removeButton.addEventListener("click", () => removeService(Number(s.id || s.service_id)));
    }
  } catch (error) {'''
    text = text.replace(marker, replacement, 1)
else:
    text = text.replace("Remove service", "Remove flight route")

# Dialog X close robustness.
close_helper = r'''
function setupDialogCloseButtons() {
  document.querySelectorAll("dialog .close-button, dialog [data-dialog-close]").forEach(button => {
    if (button.dataset.closeBound) {
      return;
    }

    button.dataset.closeBound = "true";
    button.setAttribute("type", "button");

    button.addEventListener("click", event => {
      event.preventDefault();
      button.closest("dialog")?.close();
    });
  });
}
'''
if "function setupDialogCloseButtons(" not in text:
    text += "\n" + close_helper + "\n"

# Call setup close on DOM ready and after dynamic dialog creation.
if "setupDialogCloseButtons();" not in text:
    text = text.replace("await loadRoutes();", "setupDialogCloseButtons();\n  await loadRoutes();", 1)

# If ensureAircraftModelDialog creates buttons, call setup after append.
text = text.replace(
"  document.body.appendChild(dialog);\n  return dialog;",
"  document.body.appendChild(dialog);\n  setupDialogCloseButtons();\n  return dialog;"
)

path.write_text(text, encoding="utf-8")
print("OK: routes.js labels, remove, conditional start and dialog close patched.")
