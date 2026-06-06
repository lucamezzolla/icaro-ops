#!/usr/bin/env python3
from pathlib import Path
import re

path = Path("routes.html")
text = path.read_text(encoding="utf-8")

text = text.replace('id="flightType" name="flight_type"', 'id="serviceType" name="service_type"')
text = text.replace('id="flightType"', 'id="serviceType"')
text = text.replace('name="flight_type"', 'name="service_type"')
text = text.replace("Service type", "Flight type")

text = text.replace('<option value="SCHEDULED" selected>Scheduled</option>', '<option value="SCHEDULED">Scheduled</option>')
text = text.replace('<option value="ON_DEMAND">On demand / non-scheduled</option>', '<option value="ON_DEMAND" selected>On demand / non-scheduled</option>')
text = text.replace('<option value="ON_DEMAND" selected selected>', '<option value="ON_DEMAND" selected>')

text = re.sub(r'(<input[^>]*id="scheduledTime"[^>]*value=")[^"]*("[^>]*>)', r'\1\2', text)
text = text.replace('required value="" disabled type="time"', 'value="" disabled type="time"')
text = text.replace('disabled disabled', 'disabled')

path.write_text(text, encoding="utf-8")
print("OK: routes.html now uses #serviceType and label Flight type.")
