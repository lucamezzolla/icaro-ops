#!/usr/bin/env python3
from pathlib import Path

targets = [
    Path("src/js/fleet.js"),
    Path("src/js/fleet-market-table-dialog.js"),
]

broken_patterns = [
    'header.textContent.trim().toUpperCase() === );',
    'header.textContent.trim().toUpperCase() ===);',
    'header.textContent.trim().toUpperCase()==="");',
    'header.textContent.trim().toUpperCase() === "" );',
]

fixed = 'header.textContent.trim().toUpperCase() === "BUY RULE");'

changed_any = False

for path in targets:
    if not path.exists():
        print(f"SKIP: {path} not found")
        continue

    text = path.read_text(encoding="utf-8")
    original = text

    for broken in broken_patterns:
        text = text.replace(broken, fixed)

    if text != original:
        path.write_text(text, encoding="utf-8")
        changed_any = True
        print(f"OK: fixed BUY RULE syntax in {path}")
    else:
        print(f"OK: no syntax replacement needed in {path}")

if not changed_any:
    print("NOTE: no files changed. Run grep to inspect the exact broken line:")
    print("grep -R \"toUpperCase() ===\" -n src/js/fleet.js src/js/fleet-market-table-dialog.js")
