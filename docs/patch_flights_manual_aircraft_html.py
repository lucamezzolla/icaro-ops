#!/usr/bin/env python3
from pathlib import Path

path = Path("routes.html")
text = path.read_text(encoding="utf-8")

if 'id="ownedAircraftModelChoices"' not in text:
    marker = '''          <label>
            Ticket price'''
    block = '''          <fieldset class="form-fieldset">
            <legend>Airplanes for this flight</legend>
            <p class="muted">
              Select the airplane models from your owned fleet that may operate this flight.
              Icaro Ops will not auto-pick theoretical aircraft here.
            </p>
            <div id="ownedAircraftModelChoices" class="choice-list">
              <p class="muted">Open the dialog to load owned airplanes.</p>
            </div>
          </fieldset>

'''
    if marker in text:
        text = text.replace(marker, block + marker, 1)
    else:
        raise SystemExit("Could not find Ticket price label insertion point in routes.html")

path.write_text(text, encoding="utf-8")
print("OK: routes.html has manual owned-airplane selector.")
