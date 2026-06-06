#!/usr/bin/env python3
from pathlib import Path
import re

path = Path("src/js/routes.js")
text = path.read_text(encoding="utf-8")

# Replace direct service_code display in table with public short code.
text = text.replace(
    '${escapeHtml(service.service_code)}',
    '${escapeHtml(publicFlightCode(service))}'
)

# Keep route/secondary line as internal code only if useful.
text = text.replace(
    '${escapeHtml(service.route_code)}',
    '${escapeHtml(service.service_code || service.route_code || "")}'
)

# Details: public code should be short; service_code becomes internal code.
text = text.replace(
    '["Service code", s.service_code]',
    '["Flight code", publicFlightCode(s)]'
)

text = text.replace(
    '["Internal code", s.service_code]',
    '["Internal code", s.service_code]'
)

# If previous patch replaced Route code with Flight code but still uses route_code, fix it.
text = text.replace(
    '["Flight code", s.flight_route_code || s.route_public_code || s.route_code]',
    '["Flight code", publicFlightCode(s)]'
)

helper = r'''
function publicFlightCode(row) {
  const explicitCode = row.flight_route_code || row.public_flight_code;

  if (explicitCode && !String(explicitCode).match(/^[A-Z]{3}-[0-9]{4}-/)) {
    return explicitCode;
  }

  const internal = String(row.service_code || "");
  const match = internal.match(/^([A-Z]{3}-[0-9]{4})-/);

  if (match) {
    return match[1];
  }

  return internal || row.route_code || "-";
}
'''

if "function publicFlightCode(" not in text:
    marker = "function serviceScheduleLabel("
    pos = text.find(marker)
    if pos != -1:
        text = text[:pos] + helper + "\n" + text[pos:]
    else:
        text += "\n" + helper + "\n"

path.write_text(text, encoding="utf-8")
print("OK: routes.js displays short public flight codes.")
