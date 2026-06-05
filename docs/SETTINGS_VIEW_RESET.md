# Settings view with development reset

This patch converts Settings from a map popup/link placeholder into a real page.

## Files

```text
settings.html
src/css/settings.css
src/js/settings.js
docs/SETTINGS_VIEW_RESET.md
```

## Apply

```bash
cd /home/luca/Documenti/html/icaro-ops
unzip -o /home/luca/Scaricati/icaro-ops-settings-view-reset-patch.zip
```

## Update navigation

Run this command to make Settings point to `settings.html` in all main views:

```bash
python3 - <<'PY'
from pathlib import Path
import re

pages = {
    "index.html": "Map",
    "fleet.html": "Fleet",
    "staff.html": "Staff",
    "routes.html": "Routes",
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
        ("Mailbox", "mailbox.html"),
        ("Finance", "#"),
        ("Settings", "settings.html"),
    ]

    lines = ["        <nav>"]
    for label, href in items:
        cls = ' class="active"' if label == active else ""
        lines.append(f'          <a href="{href}"{cls}>{label}</a>')
    lines.append("        </nav>")
    return "\\n".join(lines)

for filename, active in pages.items():
    path = Path(filename)
    if not path.exists():
        print(f"SKIP: {filename}")
        continue

    text = path.read_text(encoding="utf-8")
    text_new = re.sub(r'<nav>.*?</nav>', nav_for(active), text, count=1, flags=re.S)

    if text_new != text:
        path.write_text(text_new, encoding="utf-8")
        print(f"OK: updated nav in {filename}")
    else:
        print(f"WARN: nav not changed in {filename}")
PY
```

## Remove/ignore old map popup

If `dashboard-map.js` still contains a Settings popup handler, it can stay unused, but the preferred behavior is now:

```text
Settings menu item -> settings.html
```

## Development reset

The Settings page includes a destructive development reset section.

It calls:

```text
api/public/dev/reset-my-data.php
```

So make sure the previous dev reset patch is installed.

The user must type:

```text
RESET_MY_ICARO_OPS_DATA
```

Then confirm twice.

The endpoint remains local-only.
