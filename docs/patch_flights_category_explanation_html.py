#!/usr/bin/env python3
from pathlib import Path

path = Path("routes.html")
text = path.read_text(encoding="utf-8")

if 'id="routeCategory"' not in text:
    service_type_label = '''          <label>
            Service type'''
    insert = '''          <label>
            Flight category
            <select id="routeCategory" name="route_category_code">
              <option value="">Automatic</option>
              <option value="DOM">Domestic passenger</option>
              <option value="INT">International passenger</option>
              <option value="CHT">Charter</option>
              <option value="HEL">Helicopter</option>
              <option value="CGO">Cargo</option>
              <option value="MIL">Military</option>
              <option value="RES">Rescue</option>
              <option value="TRN">Training</option>
              <option value="POS">Positioning / ferry</option>
            </select>
          </label>

'''
    if service_type_label in text:
        text = text.replace(service_type_label, insert + service_type_label, 1)

if 'id="flightTypeExplanation"' not in text:
    marker = '''          </label>

          <label>
            Scheduled departure UTC'''
    explanation = '''          </label>
          <p id="flightTypeExplanation" class="muted">
            On-demand flight: manual non-scheduled flight that can be started when compatible aircraft and crew are available.
          </p>

          <label>
            Scheduled departure UTC'''
    text = text.replace(marker, explanation, 1)

path.write_text(text, encoding="utf-8")
print("OK: routes.html adds category and flight type explanation.")
