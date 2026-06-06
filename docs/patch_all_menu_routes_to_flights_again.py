#!/usr/bin/env python3
from pathlib import Path
import re

for path in Path(".").glob("*.html"):
    text = path.read_text(encoding="utf-8")
    original = text

    text = re.sub(r'(href=["\']routes\.html["\'][^>]*>\s*)(Routes)(\s*<)', r'\1Flights\3', text, flags=re.I)
    text = text.replace("<span>Routes</span>", "<span>Flights</span>")
    text = text.replace(">Routes<", ">Flights<")
    text = text.replace("Icaro Ops - Routes", "Icaro Ops - Flights")

    if text != original:
        path.write_text(text, encoding="utf-8")
        print(f"OK: menu label fixed in {path}")

print("Done.")
