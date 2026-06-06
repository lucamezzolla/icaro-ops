#!/usr/bin/env python3
from pathlib import Path

scripts = {
    "fleet.html": '<script src="src/js/fleet-market-table-dialog.js"></script>',
    "staff.html": '<script src="src/js/staff-hiring-table-dialog.js"></script>',
}

for filename, script_tag in scripts.items():
    path = Path(filename)

    if not path.exists():
        print(f"SKIP: {filename} not found")
        continue

    text = path.read_text(encoding="utf-8")

    if script_tag in text:
        print(f"OK: {filename} already includes script")
        continue

    if "</body>" in text:
        text = text.replace("</body>", f"  {script_tag}\n</body>")
    else:
        text += "\n" + script_tag + "\n"

    path.write_text(text, encoding="utf-8")
    print(f"OK: added script to {filename}")
