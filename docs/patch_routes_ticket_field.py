#!/usr/bin/env python3
from pathlib import Path

path = Path("routes.html")
text = path.read_text(encoding="utf-8")

text = text.replace('value="250.00"', 'value="0.00"')
text = text.replace('value="250"', 'value="0.00"')

old = '''          <label>
            Ticket price
            <input id="ticketPrice" name="ticket_price" type="number" min="0" step="0.01" value="0.00" required>
          </label>'''

new = '''          <label>
            Ticket price
            <input id="ticketPrice" name="ticket_price" type="number" min="0" step="0.01" value="0.00" required>
            <small class="muted">Starts at 0. After origin and destination are filled, Icaro Ops suggests a modifiable price.</small>
          </label>'''

if old in text:
    text = text.replace(old, new)

path.write_text(text, encoding="utf-8")
print("OK: routes HTML patched.")
