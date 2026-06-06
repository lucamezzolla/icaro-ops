#!/usr/bin/env python3
from pathlib import Path

path = Path("src/js/routes.js")
text = path.read_text(encoding="utf-8")

text = text.replace(
'''    service_type: serviceType,
    flight_type: serviceType,
    origin_airport_icao_code:''',
'''    service_type: serviceType,
    flight_type: serviceType,
    route_category_code: document.querySelector("#routeCategory")?.value || "",
    origin_airport_icao_code:'''
)

if "setupFlightTypeExplanation();" not in text:
    text = text.replace("setupServiceTypeToggle();", "setupServiceTypeToggle();\n  setupFlightTypeExplanation();", 1)

helper = r'''
function setupFlightTypeExplanation() {
  const serviceType = document.querySelector("#serviceType");
  const explanation = document.querySelector("#flightTypeExplanation");

  if (!serviceType || !explanation) {
    return;
  }

  const refresh = () => {
    if (serviceType.value === "SCHEDULED") {
      explanation.textContent = "Scheduled flight: recurring planned flight with a fixed UTC departure time. The aircraft must be available at the origin airport when departure time arrives.";
    } else {
      explanation.textContent = "On-demand flight: manual non-scheduled flight that can be started when compatible aircraft and crew are available. Useful for extra income, but it may interfere with later scheduled flights.";
    }
  };

  if (!serviceType.dataset.explanationBound) {
    serviceType.dataset.explanationBound = "true";
    serviceType.addEventListener("change", refresh);
  }

  refresh();
}
'''

if "function setupFlightTypeExplanation(" not in text:
    marker = "function setupServiceTypeToggle()"
    pos = text.find(marker)
    text = text[:pos] + helper + "\n\n" + text[pos:] if pos != -1 else text + "\n" + helper

path.write_text(text, encoding="utf-8")
print("OK: routes.js sends route category and explains scheduled/on-demand.")
