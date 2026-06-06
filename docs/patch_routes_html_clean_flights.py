#!/usr/bin/env python3
from pathlib import Path
import re

path = Path("routes.html")
text = path.read_text(encoding="utf-8")

# Remove the bad sentence and replace surrounding wording with clean Flights wording.
text = text.replace(
    "A flight is not a flight. Details show air route, flight policy and generated flight instances.",
    "Create on-demand or scheduled flights and open details for operational rules and generated flight instances."
)

text = text.replace(
    "Scheduled flights are commercial offers over abstract air routes. Real flights are generated later and dispatched with compatible aircraft.",
    "Create on-demand or scheduled flights. Real flight instances are dispatched with compatible aircraft and crew."
)

text = text.replace(
    "Manage scheduled flights separately from abstract routes and real flight instances.",
    "Manage on-demand and scheduled flights."
)

text = text.replace("Scheduled flights", "Flights")
text = text.replace("Add scheduled flight", "Add flight")
text = text.replace("Create route", "Create flight")
text = text.replace("Route details", "Flight details")
text = text.replace('<p class="eyebrow">Route</p>', '<p class="eyebrow">Flight</p>')

# Align select id with the JS and keep the visible label as Flight type.
text = text.replace('id="flightType" name="flight_type"', 'id="serviceType" name="service_type"')
text = text.replace('id="flightType"', 'id="serviceType"')
text = text.replace('name="flight_type"', 'name="service_type"')
text = text.replace("Service type", "Flight type")

# On-demand is the default, but scheduled must remain selectable.
text = text.replace('<option value="SCHEDULED" selected>Scheduled</option>', '<option value="SCHEDULED">Scheduled</option>')
text = text.replace('<option value="ON_DEMAND">On demand / non-scheduled</option>', '<option value="ON_DEMAND" selected>On demand / non-scheduled</option>')
text = text.replace('<option value="ON_DEMAND" selected selected>', '<option value="ON_DEMAND" selected>')

# Scheduled time starts disabled because On-demand is default.
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

text = text.replace('disabled disabled', 'disabled')

path.write_text(text, encoding="utf-8")
print("OK: routes.html cleaned and flight type select fixed.")
