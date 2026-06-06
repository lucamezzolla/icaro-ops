#!/usr/bin/env python3
from pathlib import Path

path = Path("src/js/routes.js")
text = path.read_text(encoding="utf-8")

# Table columns: remove Required class and Status, add Scheduled and Preferred models.
text = text.replace(
'''      <td>${escapeHtml(service.scheduled_departure_time_utc || "-")}</td>
      <td>${escapeHtml(service.required_aircraft_class || "-")}</td>
      <td>${escapeHtml(service.manufacturer || "")} ${escapeHtml(service.model_name || "")}</td>
      <td>${money(service.ticket_price)} ${escapeHtml(service.currency_code || "")}</td>
      <td><span class="badge ${service.status === "ACTIVE" ? "good" : "warn"}">${escapeHtml(service.status || "-")}</span></td>''',
'''      <td>${serviceScheduleLabel(service)}</td>
      <td>${modelCodesLabel(service)}</td>
      <td>${money(service.ticket_price)} ${escapeHtml(service.currency_code || "")}</td>'''
)

# Empty table colspan from 8 to 6 if present.
text = text.replace('colspan="8"', 'colspan="6"')

# Add helper functions.
helper = r'''
function serviceScheduleLabel(service) {
  const type = service.service_type || (service.scheduled_departure_time_utc ? "SCHEDULED" : "ON_DEMAND");

  if (type === "ON_DEMAND") {
    return "On demand";
  }

  return service.scheduled_departure_time_utc || "-";
}

function modelCodesLabel(service) {
  return escapeHtml(
    service.compatible_aircraft_model_codes ||
    service.model_code ||
    "C208B_GRAND_CARAVAN_EX"
  );
}
'''

if "function serviceScheduleLabel(" not in text:
    marker = "function openAddRouteDialog()"
    pos = text.find(marker)
    if pos != -1:
        text = text[:pos] + helper + "\n\n" + text[pos:]
    else:
        text += "\n" + helper + "\n"

# Route form payload includes service_type.
text = text.replace(
'''    scheduled_departure_time_utc: document.querySelector("#scheduledTime").value,
    ticket_price: Number(document.querySelector("#ticketPrice").value)''',
'''    service_type: document.querySelector("#serviceType")?.value || "SCHEDULED",
    scheduled_departure_time_utc: document.querySelector("#scheduledTime").value,
    ticket_price: Number(document.querySelector("#ticketPrice").value)'''
)

# open dialog default.
text = text.replace(
'''  document.querySelector("#scheduledTime").value = "10:00";
  document.querySelector("#ticketPrice").value = "0.00";''',
'''  if (document.querySelector("#serviceType")) {
    document.querySelector("#serviceType").value = "SCHEDULED";
  }
  document.querySelector("#scheduledTime").value = "10:00";
  document.querySelector("#scheduledTime").disabled = false;
  document.querySelector("#ticketPrice").value = "0.00";'''
)

# Bind service type change.
if "setupServiceTypeToggle();" not in text:
    text = text.replace("setupTicketSuggestion();", "setupTicketSuggestion();\n  setupServiceTypeToggle();")

toggle = r'''
function setupServiceTypeToggle() {
  const serviceType = document.querySelector("#serviceType");
  const scheduledTime = document.querySelector("#scheduledTime");

  if (!serviceType || !scheduledTime || serviceType.dataset.bound) {
    return;
  }

  serviceType.dataset.bound = "true";

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

  serviceType.addEventListener("change", refresh);
  refresh();
}
'''

if "function setupServiceTypeToggle(" not in text:
    marker = "function setupTicketSuggestion()"
    pos = text.find(marker)
    if pos != -1:
        text = text[:pos] + toggle + "\n\n" + text[pos:]
    else:
        text += "\n" + toggle + "\n"

# Detail display updates.
text = text.replace('["Departure UTC", s.scheduled_departure_time_utc],', '["Scheduled", serviceScheduleLabel(s)],')
text = text.replace('["Status", s.service_status],', '["Service type", s.service_type || "-"],')
text = text.replace('["Required aircraft class", s.required_aircraft_class],', '["Compatible models", s.compatible_aircraft_model_codes || s.model_code || "-"],')
text = text.replace('["Preferred model", `${s.manufacturer || "-"} ${s.model_name || ""}`],', '["Preferred model", `${s.manufacturer || "-"} ${s.model_name || ""}`],')

path.write_text(text, encoding="utf-8")
print("OK: routes.js table uses Scheduled and Preferred models.")
