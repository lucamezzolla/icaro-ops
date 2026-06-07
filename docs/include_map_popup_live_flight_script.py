#!/usr/bin/env python3
from pathlib import Path

script = '<script src="src/js/map-active-flight-popup.js"></script>'

# Include only in pages that can reasonably contain the map.
# If your map is in a different HTML file, add it here.
candidates = [
    Path("dashboard.html"),
    Path("map.html"),
    Path("operations.html"),
    Path("index.html"),
]

for path in candidates:
    if not path.exists():
        continue

    text = path.read_text(encoding="utf-8")

    if script in text:
        print(f"OK: {path} already includes map popup script")
        continue

    if "</body>" in text:
        text = text.replace("</body>", f"  {script}\n</body>")
    else:
        text += "\n" + script + "\n"

    path.write_text(text, encoding="utf-8")
    print(f"OK: added map popup live script to {path}")
