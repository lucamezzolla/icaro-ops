#!/usr/bin/env python3
from pathlib import Path
import re

path = Path("src/js/routes.js")
text = path.read_text(encoding="utf-8")

if "function getFlightTypeSelect()" not in text:
    helper = '''
function getFlightTypeSelect() {
  return document.querySelector("#serviceType") || document.querySelector("#flightType");
}
'''
    insert_after = 'let lastSuggestedTicketPrice = null;'
    if insert_after in text:
        text = text.replace(insert_after, insert_after + "\n" + helper, 1)
    else:
        text = helper + "\n" + text

text = text.replace('document.querySelector("#serviceType")', 'getFlightTypeSelect()')
text = text.replace('getFlightTypeSelect() || getFlightTypeSelect()', 'getFlightTypeSelect()')

toggle_fn = '''function setupServiceTypeToggle() {
  const serviceType = getFlightTypeSelect();
  const scheduledTime = document.querySelector("#scheduledTime");

  if (!serviceType || !scheduledTime) {
    return;
  }

  const refresh = () => {
    const isScheduled = serviceType.value === "SCHEDULED";

    if (isScheduled) {
      scheduledTime.disabled = false;
      scheduledTime.required = true;
      scheduledTime.removeAttribute("disabled");
      scheduledTime.removeAttribute("aria-disabled");

      if (!scheduledTime.value) {
        scheduledTime.value = "10:00";
      }
    } else {
      scheduledTime.value = "";
      scheduledTime.required = false;
      scheduledTime.disabled = true;
      scheduledTime.setAttribute("disabled", "disabled");
      scheduledTime.setAttribute("aria-disabled", "true");
    }
  };

  if (!serviceType.dataset.bound) {
    serviceType.dataset.bound = "true";
    serviceType.addEventListener("change", refresh);
    serviceType.addEventListener("input", refresh);
  }

  refresh();
}'''

if "function setupServiceTypeToggle()" in text:
    text = re.sub(r"function setupServiceTypeToggle\(\)\s*\{.*?\n\}", toggle_fn, text, count=1, flags=re.S)
else:
    text += "\n" + toggle_fn + "\n"

payload_fn = '''function normalizedFlightFormPayload() {
  const serviceType = getFlightTypeSelect()?.value || "ON_DEMAND";
  const scheduledTimeField = document.querySelector("#scheduledTime");
  const scheduledTime = serviceType === "SCHEDULED"
    ? (scheduledTimeField?.value || "10:00")
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

if "function normalizedFlightFormPayload()" in text:
    text = re.sub(r"function normalizedFlightFormPayload\(\)\s*\{.*?\n\}", payload_fn, text, count=1, flags=re.S)
else:
    text += "\n" + payload_fn + "\n"

if "function routeFormPayload()" in text:
    text = re.sub(
        r"function routeFormPayload\(\)\s*\{.*?\n\}",
        "function routeFormPayload() {\n  return normalizedFlightFormPayload();\n}",
        text,
        count=1,
        flags=re.S
    )

path.write_text(text, encoding="utf-8")
print("OK: routes.js now controls the real flight type select.")
