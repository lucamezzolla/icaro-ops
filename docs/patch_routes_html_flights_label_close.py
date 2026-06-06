#!/usr/bin/env python3
from pathlib import Path
import re

path = Path("routes.html")
text = path.read_text(encoding="utf-8")

# Services -> Flights in visible labels.
replacements = {
    "Services over Air Routes": "Flights over Air Routes",
    "Services": "Flights",
    "services": "flights",
    "service": "flight",
    "Add service": "Add flight",
    "Scheduled services": "Flights",
    "Service / Air route": "Flight / Air route",
    "Add scheduled service": "Add flight",
    "Scheduled service": "Flight route",
    "scheduled service": "flight route",
}

for old, new in replacements.items():
    text = text.replace(old, new)

# Normalize headers.
new_head = '''<thead>
                <tr>
                  <th>Flight / Air route</th>
                  <th>Route</th>
                  <th>Scheduled</th>
                  <th>Airplanes</th>
                  <th></th>
                </tr>
              </thead>'''

text = re.sub(
    r"<thead>\s*<tr>.*?</tr>\s*</thead>",
    new_head,
    text,
    count=1,
    flags=re.S
)

# Make every close-button a reliable type=button.
text = re.sub(
    r'<button([^>]*class="[^"]*close-button[^"]*"[^>]*)>',
    lambda m: '<button type="button"' + m.group(1) + '>' if 'type=' not in m.group(1) else '<button' + m.group(1) + '>',
    text
)

path.write_text(text, encoding="utf-8")
print("OK: routes.html labels and close buttons patched.")
