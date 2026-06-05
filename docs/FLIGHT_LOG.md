# Flight Log

Adds a Flight Log page with compact history table and detail dialog.

## Files

```text
flight-log.html
src/css/flight-log.css
src/js/flight-log.js
api/public/flights/log.php
api/public/flights/detail.php
docs/FLIGHT_LOG.md
```

## Apply

```bash
cd /home/luca/Documenti/html/icaro-ops
unzip -o /home/luca/Scaricati/icaro-ops-flight-log-patch.zip
```

## Open

```text
http://127.0.0.1:8080/flight-log.html
```

## Update navigation

```bash
python3 - <<'PY'
from pathlib import Path
import re

pages = {
    "index.html": "Map",
    "fleet.html": "Fleet",
    "staff.html": "Staff",
    "routes.html": "Routes",
    "flight-log.html": "Flight Log",
    "mailbox.html": "Mailbox",
    "maintenance.html": "",
    "settings.html": "Settings",
}

def nav_for(active):
    items = [
        ("Map", "index.html"),
        ("Fleet", "fleet.html"),
        ("Staff", "staff.html"),
        ("Routes", "routes.html"),
        ("Flight Log", "flight-log.html"),
        ("Mailbox", "mailbox.html"),
        ("Finance", "#"),
        ("Settings", "settings.html"),
    ]
    lines = ["        <nav>"]
    for label, href in items:
        cls = ' class="active"' if label == active else ""
        lines.append(f'          <a href="{href}"{cls}>{label}</a>')
    lines.append("        </nav>")
    return "\n".join(lines)

for filename, active in pages.items():
    path = Path(filename)
    if not path.exists():
        print(f"SKIP: {filename}")
        continue
    text = path.read_text(encoding="utf-8")
    new_text = re.sub(r'<nav>.*?</nav>', nav_for(active), text, count=1, flags=re.S)
    if new_text != text:
        path.write_text(new_text, encoding="utf-8")
        print(f"OK: updated nav in {filename}")
    else:
        print(f"WARN: nav not changed in {filename}")
PY
```
