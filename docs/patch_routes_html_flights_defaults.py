#!/usr/bin/env python3
from pathlib import Path
import re

path = Path("routes.html")
text = path.read_text(encoding="utf-8")

text = text.replace("Flights over Air Routes", "Flights")
text = text.replace("Routes", "Flights")

text = text.replace('<option value="SCHEDULED" selected>Scheduled</option>', '<option value="SCHEDULED">Scheduled</option>')
text = text.replace('<option value="ON_DEMAND">On demand / non-scheduled</option>', '<option value="ON_DEMAND" selected>On demand / non-scheduled</option>')
text = text.replace('<option value="ON_DEMAND" selected selected>', '<option value="ON_DEMAND" selected>')

text = re.sub(r'(<input[^>]*id="scheduledTime"[^>]*value=")[^"]*("[^>]*>)', r'\1\2', text)

text = re.sub(
    r'(<input[^>]*id="scheduledTime"[^>]*)(>)',
    lambda m: m.group(1) + (' disabled' if 'disabled' not in m.group(1) else '') + m.group(2),
    text,
    count=1
)

path.write_text(text, encoding="utf-8")
print("OK: routes.html labels/defaults fixed.")
