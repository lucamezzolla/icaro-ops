#!/usr/bin/env python3
from pathlib import Path
import re

path = Path("routes.html")
text = path.read_text(encoding="utf-8")

text = text.replace("Flights over Air Routes", "Flights")
text = text.replace("Flights over air routes", "Flights")
text = text.replace("Flight routes", "Flights")
text = text.replace("Flight route", "Flight")
text = text.replace("flight route", "flight")
text = text.replace("Add flight route", "Add flight")

# Make service type default ON_DEMAND in the select.
text = text.replace('<option value="SCHEDULED" selected>Scheduled</option>', '<option value="SCHEDULED">Scheduled</option>')
text = text.replace('<option value="ON_DEMAND">On demand / non-scheduled</option>', '<option value="ON_DEMAND" selected>On demand / non-scheduled</option>')

# If no ON_DEMAND option is selected because HTML differs, enforce with regex.
text = re.sub(r'<option value="ON_DEMAND"(?![^>]*selected)', '<option value="ON_DEMAND" selected', text, count=1)

# Scheduled time starts disabled and empty.
text = re.sub(
    r'(<input[^>]*id="scheduledTime"[^>]*value=")[^"]*("[^>]*>)',
    r'\1\2',
    text
)
text = re.sub(
    r'(<input[^>]*id="scheduledTime"[^>]*)(>)',
    lambda m: m.group(1) + (' disabled' if 'disabled' not in m.group(1) else '') + m.group(2),
    text,
    count=1
)

# Header stays simple.
text = text.replace("<h1>Flights over Air Routes</h1>", "<h1>Flights</h1>")

path.write_text(text, encoding="utf-8")
print("OK: routes.html defaults to on-demand and title is Flights.")
