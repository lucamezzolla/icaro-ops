#!/usr/bin/env python3
from pathlib import Path

script = '<script src="src/js/active-flight-timer-dialog.js"></script>'

for filename in ["dashboard.html", "fleet.html", "routes.html", "flight-log.html"]:
    path = Path(filename)

    if not path.exists():
        print(f"SKIP: {filename} not found")
        continue

    text = path.read_text(encoding="utf-8")

    if script in text:
        print(f"OK: {filename} already includes active flight timer script")
        continue

    if "</body>" in text:
        text = text.replace("</body>", f"  {script}\n</body>")
    else:
        text += "\n" + script + "\n"

    path.write_text(text, encoding="utf-8")
    print(f"OK: added active flight timer script to {filename}")
