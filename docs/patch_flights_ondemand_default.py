#!/usr/bin/env python3
from pathlib import Path
import re

path = Path("src/js/routes.js")
text = path.read_text(encoding="utf-8")

# Title/labels cleanup.
text = text.replace("Flights over Air Routes", "Flights")
text = text.replace("Flights over air routes", "Flights")
text = text.replace("Flight route", "Flight")
text = text.replace("flight route", "flight")
text = text.replace("Add flight route", "Add flight")
text = text.replace("Remove flight route", "Remove flight")

# Default creation must be ON_DEMAND, with scheduled time disabled and empty.
open_pattern = r'''function openAddRouteDialog\(\)\s*\{.*?\n\}'''
open_replacement = '''function openAddRouteDialog() {
  const dialog = document.querySelector("#routeDialog");

  if (!dialog) {
    showError("Flight dialog not found.");
    return;
  }

  document.querySelector("#originAirport").value = "";
  document.querySelector("#destinationAirport").value = "";

  const serviceType = document.querySelector("#serviceType");
  const scheduledTime = document.querySelector("#scheduledTime");

  if (serviceType) {
    serviceType.value = "ON_DEMAND";
  }

  if (scheduledTime) {
    scheduledTime.value = "";
    scheduledTime.disabled = true;
    scheduledTime.required = false;
  }

  document.querySelector("#ticketPrice").value = "0.00";
  document.querySelector("#routePreviewPanel").hidden = true;
  document.querySelector("#routeDialogError").hidden = true;

  setupServiceTypeToggle();
  dialog.showModal();
}'''

text = re.sub(open_pattern, open_replacement, text, count=1, flags=re.S)

# Payload must ignore stale scheduled time when ON_DEMAND.
payload_pattern = r'''function routeFormPayload\(\)\s*\{.*?\n\}'''
payload_replacement = '''function routeFormPayload() {
  const serviceType = document.querySelector("#serviceType")?.value || "ON_DEMAND";
  const scheduledTime = serviceType === "SCHEDULED"
    ? document.querySelector("#scheduledTime").value
    : "";

  return {
    service_type: serviceType,
    flight_type: serviceType,
    origin_airport_icao_code: document.querySelector("#originAirport").value.trim().toUpperCase(),
    destination_airport_icao_code: document.querySelector("#destinationAirport").value.trim().toUpperCase(),
    scheduled_departure_time_utc: scheduledTime,
    ticket_price: Number(document.querySelector("#ticketPrice").value)
  };
}'''

text = re.sub(payload_pattern, payload_replacement, text, count=1, flags=re.S)

# Service type toggle: default ON_DEMAND and robust disable/enable.
toggle_pattern = r'''function setupServiceTypeToggle\(\)\s*\{.*?\n\}'''
toggle_replacement = '''function setupServiceTypeToggle() {
  const serviceType = document.querySelector("#serviceType");
  const scheduledTime = document.querySelector("#scheduledTime");

  if (!serviceType || !scheduledTime) {
    return;
  }

  const refresh = () => {
    const isScheduled = serviceType.value === "SCHEDULED";
    scheduledTime.disabled = !isScheduled;
    scheduledTime.required = isScheduled;

    if (!isScheduled) {
      scheduledTime.value = "";
    } else if (!scheduledTime.value) {
      scheduledTime.value = "10:00";
    }
  };

  if (!serviceType.dataset.bound) {
    serviceType.dataset.bound = "true";
    serviceType.addEventListener("change", refresh);
  }

  refresh();
}'''

if "function setupServiceTypeToggle" in text:
    text = re.sub(toggle_pattern, toggle_replacement, text, count=1, flags=re.S)
else:
    text += "\n" + toggle_replacement + "\n"

# Start button should appear for ON_DEMAND only. Ensure helper is correct.
if "function isOnDemandService" in text:
    text = re.sub(
        r'''function isOnDemandService\(service\)\s*\{.*?\n\}''',
        '''function isOnDemandService(service) {
  const type = service.service_type || (service.scheduled_departure_time_utc ? "SCHEDULED" : "ON_DEMAND");
  return type === "ON_DEMAND";
}''',
        text,
        count=1,
        flags=re.S
    )

# If duplicate conditional start buttons were created, collapse repeated empty template line patterns a bit.
text = text.replace(
'''          ${isOnDemandService(service) ? `<button type="button" data-start-service="${service.service_id}" class="secondary">Start flight now</button>` : ""}
          ${isOnDemandService(service) ? `<button type="button" data-start-service="${service.service_id}" class="secondary">Start flight now</button>` : ""}''',
'''          ${isOnDemandService(service) ? `<button type="button" data-start-service="${service.service_id}" class="secondary">Start flight now</button>` : ""}'''
)

path.write_text(text, encoding="utf-8")
print("OK: ON_DEMAND default and flight labels fixed.")
