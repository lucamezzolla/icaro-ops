#!/usr/bin/env python3
from pathlib import Path
import re

path = Path("routes.html")
text = path.read_text(encoding="utf-8")

# Header replacements, tolerant.
text = text.replace("<th>Required class</th>", "<th>Preferred models</th>")
text = text.replace("<th>Aircraft</th>", "<th>Preferred models</th>")
text = text.replace("<th>Preferred model</th>", "<th>Preferred models</th>")
text = text.replace("<th>Status</th>", "")
text = text.replace("<th>Departure UTC</th>", "<th>Scheduled</th>")
text = text.replace("<th>Departure</th>", "<th>Scheduled</th>")
text = text.replace("<th>Scheduled UTC</th>", "<th>Scheduled</th>")

# Insert service type select before scheduled time if not present.
if 'id="serviceType"' not in text:
    marker = '''          <label>
            Scheduled departure UTC'''
    insert = '''          <label>
            Service type
            <select id="serviceType" name="service_type">
              <option value="SCHEDULED" selected>Scheduled</option>
              <option value="ON_DEMAND">On demand / non-scheduled</option>
            </select>
          </label>

'''
    if marker in text:
        text = text.replace(marker, insert + marker)
    else:
        marker2 = '''          <label>
            Departure UTC'''
        text = text.replace(marker2, insert + marker2)

# Improve scheduled time label.
text = text.replace("Scheduled departure UTC", "Scheduled departure UTC")
text = text.replace("Departure UTC", "Scheduled departure UTC")

path.write_text(text, encoding="utf-8")
print("OK: routes.html supports scheduled/on-demand creation and simplified columns.")
