#!/usr/bin/env python3
from pathlib import Path

path = Path("src/js/routes.js")
text = path.read_text(encoding="utf-8")

if 'startServiceFlight: "api/public/flights/start-service-now.php"' not in text:
    text = text.replace(
        'preview: "api/public/routes/preview.php"',
        'preview: "api/public/routes/preview.php",\n  startServiceFlight: "api/public/flights/start-service-now.php"'
    )

if 'data-start-service' not in text:
    text = text.replace(
'''          <button type="button" data-service-detail="${service.service_id}">Details</button>''',
'''          <button type="button" data-service-detail="${service.service_id}">Details</button>
          <button type="button" data-start-service="${service.service_id}" class="secondary">Start flight now</button>'''
    )

    text = text.replace(
'''  tbody.querySelectorAll("[data-service-detail]").forEach(button => {
    button.addEventListener("click", () => openRouteDetail(Number(button.dataset.serviceDetail)));
  });''',
'''  tbody.querySelectorAll("[data-service-detail]").forEach(button => {
    button.addEventListener("click", () => openRouteDetail(Number(button.dataset.serviceDetail)));
  });

  tbody.querySelectorAll("[data-start-service]").forEach(button => {
    button.addEventListener("click", () => startServiceFlight(Number(button.dataset.startService)));
  });'''
    )

helper = '''
async function startServiceFlight(serviceId) {
  hideError();

  if (!confirm("Create and start a real flight instance for this scheduled service now?")) {
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

    await loadRoutes();
  } catch (error) {
    showError(error.message || "Unable to start service flight.");
  }
}
'''

if "async function startServiceFlight(" not in text:
    marker = "function openAddRouteDialog()"
    pos = text.find(marker)
    if pos != -1:
        text = text[:pos] + helper + "\n\n" + text[pos:]
    else:
        text += "\n" + helper + "\n"

path.write_text(text, encoding="utf-8")
print("OK: routes.js supports Start flight now.")
