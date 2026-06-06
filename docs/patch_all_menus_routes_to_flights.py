#!/usr/bin/env python3
from pathlib import Path
import re

for path in Path(".").glob("*.html"):
    text = path.read_text(encoding="utf-8")
    original = text

    text = text.replace(">Routes<", ">Flights<")
    text = text.replace("<span>Routes</span>", "<span>Flights</span>")
    text = text.replace("Routes</title>", "Flights</title>")
    text = text.replace("Icaro Ops - Routes", "Icaro Ops - Flights")
    text = re.sub(r"(href=[\"']routes\.html[\"'][^>]*>\s*)Routes(\s*<)", r"\1Flights\2", text, flags=re.I)

    if text != original:
        path.write_text(text, encoding="utf-8")
        print(f"OK: renamed menu label in {path}")

print("Done.")
