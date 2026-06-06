#!/usr/bin/env python3
from pathlib import Path
import re

path = Path("src/js/routes.js")
text = path.read_text(encoding="utf-8")

toggle_fn = r'''function setupServiceTypeToggle() {
  const serviceType = document.querySelector("#serviceType");
  const scheduledTime = document.querySelector("#scheduledTime");

  if (!serviceType || !scheduledTime) {
    return;
  }

  const refresh = () => {
    const isScheduled = serviceType.value === "SCHEDULED";

    scheduledTime.disabled = !isScheduled;
    scheduledTime.required = isScheduled;

    if (isScheduled) {
      if (!scheduledTime.value) {
        scheduledTime.value = "10:00";
      }
      scheduledTime.removeAttribute("disabled");
    } else {
      scheduledTime.value = "";
      scheduledTime.setAttribute("disabled", "disabled");
    }
  };

  if (!serviceType.dataset.bound) {
    serviceType.dataset.bound = "true";
    serviceType.addEventListener("change", refresh);
  }

  refresh();
}'''

if "function setupServiceTypeToggle(" in text:
    text = re.sub(r"function setupServiceTypeToggle\(\)\s*\{.*?\n\}", toggle_fn, text, count=1, flags=re.S)
else:
    text += "\n" + toggle_fn + "\n"

if "setupServiceTypeToggle();" not in text:
    text = text.replace("setupTicketSuggestion();", "setupTicketSuggestion();\n  setupServiceTypeToggle();", 1)

open_fn = r'''function openAddRouteDialog() {
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
    scheduledTime.setAttribute("disabled", "disabled");
  }

  document.querySelector("#ticketPrice").value = "0.00";
  document.querySelector("#routePreviewPanel").hidden = true;
  document.querySelector("#routeDialogError").hidden = true;

  setupServiceTypeToggle();

  if (typeof setupFlightTypeExplanation === "function") {
    setupFlightTypeExplanation();
  }

  dialog.showModal();
}'''

if "function openAddRouteDialog(" in text:
    text = re.sub(r"function openAddRouteDialog\(\)\s*\{.*?\n\}", open_fn, text, count=1, flags=re.S)

payload_fn = r'''function routeFormPayload() {
  const serviceType = document.querySelector("#serviceType")?.value || "ON_DEMAND";
  const scheduledTime = serviceType === "SCHEDULED"
    ? document.querySelector("#scheduledTime").value
    : "";

  return {
    service_type: serviceType,
    flight_type: serviceType,
    route_category_code: document.querySelector("#routeCategory")?.value || "",
    origin_airport_icao_code: document.querySelector("#originAirport").value.trim().toUpperCase(),
    destination_airport_icao_code: document.querySelector("#destinationAirport").value.trim().toUpperCase(),
    scheduled_departure_time_utc: scheduledTime,
    ticket_price: Number(document.querySelector("#ticketPrice").value)
  };
}'''

if "function routeFormPayload(" in text:
    text = re.sub(r"function routeFormPayload\(\)\s*\{.*?\n\}", payload_fn, text, count=1, flags=re.S)

path.write_text(text, encoding="utf-8")
print("OK: routes.js scheduled time toggle fixed.")
