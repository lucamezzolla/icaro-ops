#!/usr/bin/env python3
from pathlib import Path

path = Path("src/js/routes.js")
text = path.read_text(encoding="utf-8")

hard_fix = r"""
/*
 * Hard fix for Flight type -> Scheduled departure UTC.
 * This controller is intentionally independent from older setupServiceTypeToggle()
 * versions, because routes.js has been patched many times during migration.
 */
function forceScheduledDepartureController() {
  const serviceType = document.querySelector("#serviceType");
  const scheduledTime = document.querySelector("#scheduledTime");

  if (!serviceType || !scheduledTime) {
    return;
  }

  const applyState = () => {
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

  if (!serviceType.dataset.hardScheduledControllerBound) {
    serviceType.dataset.hardScheduledControllerBound = "true";

    serviceType.addEventListener("change", () => {
      applyState();
    });

    serviceType.addEventListener("input", () => {
      applyState();
    });
  }

  applyState();
}

document.addEventListener("DOMContentLoaded", () => {
  forceScheduledDepartureController();

  const addButton =
    document.querySelector("#addRouteButton") ||
    document.querySelector("#addFlightButton") ||
    document.querySelector("[data-action='add-flight']");

  if (addButton && !addButton.dataset.scheduledTimeHardFixBound) {
    addButton.dataset.scheduledTimeHardFixBound = "true";
    addButton.addEventListener("click", () => {
      window.setTimeout(forceScheduledDepartureController, 0);
      window.setTimeout(forceScheduledDepartureController, 50);
    });
  }
});

document.addEventListener("click", event => {
  const target = event.target;

  if (!(target instanceof Element)) {
    return;
  }

  if (
    target.matches("#addRouteButton") ||
    target.matches("#addFlightButton") ||
    target.closest("#routeDialog")
  ) {
    window.setTimeout(forceScheduledDepartureController, 0);
  }
});
"""

if "function forceScheduledDepartureController()" not in text:
    text += "\n" + hard_fix + "\n"

payload_fix = r"""
function normalizedFlightFormPayload() {
  const serviceType = document.querySelector("#serviceType")?.value || "ON_DEMAND";
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
}
"""

if "function normalizedFlightFormPayload()" not in text:
    text += "\n" + payload_fix + "\n"

if "return normalizedFlightFormPayload();" not in text:
    marker = "function routeFormPayload()"
    idx = text.find(marker)
    if idx != -1:
        brace_start = text.find("{", idx)
        if brace_start != -1:
            depth = 0
            end = None
            for i in range(brace_start, len(text)):
                if text[i] == "{":
                    depth += 1
                elif text[i] == "}":
                    depth -= 1
                    if depth == 0:
                        end = i + 1
                        break
            if end:
                text = (
                    text[:idx]
                    + "function routeFormPayload() {\n  return normalizedFlightFormPayload();\n}\n"
                    + text[end:]
                )

path.write_text(text, encoding="utf-8")
print("OK: scheduled time hard fix installed in src/js/routes.js")
