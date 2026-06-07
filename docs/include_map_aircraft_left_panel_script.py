#!/usr/bin/env python3
from pathlib import Path

script = '<script src="src/js/map-aircraft-left-panel.js"></script>'

# Add to pages that may host the map.
for filename in ["dashboard.html", "map.html", "operations.html", "index.html", "routes.html"]:
    path = Path(filename)

    if not path.exists():
        print(f"SKIP: {filename} not found")
        continue

    text = path.read_text(encoding="utf-8")

    if script in text:
        print(f"OK: {filename} already includes left panel script")
        continue

    if "</body>" in text:
        text = text.replace("</body>", f"  {script}\n</body>")
    else:
        text += "\n" + script + "\n"

    path.write_text(text, encoding="utf-8")
    print(f"OK: added left panel script to {filename}")
