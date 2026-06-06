#!/usr/bin/env python3
from pathlib import Path

path = Path("src/js/routes.js")
text = path.read_text(encoding="utf-8")

# Prefer the public flight code in the table and details.
text = text.replace(
    '${escapeHtml(service.service_code)}',
    '${escapeHtml(service.flight_route_code || service.service_code)}'
)

text = text.replace(
    '${escapeHtml(service.route_code)}',
    '${escapeHtml(service.service_code)}'
)

text = text.replace(
    '["Service code", s.service_code]',
    '["Internal code", s.service_code]'
)

text = text.replace(
    '["Route code", s.route_code]',
    '["Flight code", s.flight_route_code || s.route_public_code || s.route_code]'
)

path.write_text(text, encoding="utf-8")
print("OK: UI now displays public flight code first.")
