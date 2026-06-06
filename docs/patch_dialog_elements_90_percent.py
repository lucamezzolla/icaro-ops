#!/usr/bin/env python3
from pathlib import Path

css_file = Path("docs/dialog_elements_90_percent_fix.css")
css = css_file.read_text(encoding="utf-8")

targets = [
    Path("src/css/routes.css"),
    Path("src/css/staff.css"),
    Path("src/css/fleet.css"),
]

for target in targets:
    if not target.exists():
        print(f"SKIP: {target} not found")
        continue

    text = target.read_text(encoding="utf-8")

    if "Force the real <dialog> elements themselves to 90% viewport size" in text:
        print(f"OK: {target} already patched")
        continue

    target.write_text(text.rstrip() + "\n\n" + css + "\n", encoding="utf-8")
    print(f"OK: patched {target}")
