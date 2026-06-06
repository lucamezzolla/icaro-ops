#!/usr/bin/env python3
from pathlib import Path
import re

path = Path("routes.html")
text = path.read_text(encoding="utf-8")

new_head = '''<thead>
                <tr>
                  <th>Service / Air route</th>
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

path.write_text(text, encoding="utf-8")
print("OK: routes.html table headers normalized.")
