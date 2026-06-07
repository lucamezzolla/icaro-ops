#!/usr/bin/env python3
from pathlib import Path

remove_scripts = [
    '<script src="src/js/map-active-flight-popup.js"></script>',
    '<script src="src/js/active-flight-clickable-enhancer.js"></script>',
    '<script src="src/js/active-flight-timer-dialog.js"></script>',
]

for html in Path(".").glob("*.html"):
    text = html.read_text(encoding="utf-8")
    original = text

    for script in remove_scripts:
        text = text.replace("  " + script + "\n", "")
        text = text.replace(script + "\n", "")
        text = text.replace(script, "")

    if text != original:
        html.write_text(text, encoding="utf-8")
        print(f"OK: removed old popup/live scripts from {html}")
