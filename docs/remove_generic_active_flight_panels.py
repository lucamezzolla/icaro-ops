#!/usr/bin/env python3
from pathlib import Path
import re

old_scripts = [
    '<script src="src/js/active-flight-clickable-enhancer.js"></script>',
    '<script src="src/js/active-flight-timer-dialog.js"></script>',
]

for html in Path(".").glob("*.html"):
    text = html.read_text(encoding="utf-8")
    original = text

    for script in old_scripts:
        text = text.replace("  " + script + "\n", "")
        text = text.replace(script + "\n", "")
        text = text.replace(script, "")

    if text != original:
        html.write_text(text, encoding="utf-8")
        print(f"OK: removed generic active flight scripts from {html}")

# Safety: if the old floating panel CSS was appended, hide it so it cannot appear even if cached.
for css_path in [Path("src/css/fleet.css"), Path("src/css/routes.css"), Path("src/css/dashboard.css")]:
    if not css_path.exists():
        continue

    css = css_path.read_text(encoding="utf-8")
    marker = "/* Disable old generic active flights panel. Live data belongs in the map popup. */"

    if marker not in css:
        css += """

""" + marker + """
#activeFlightsQuickPanel {
  display: none !important;
}
"""
        css_path.write_text(css, encoding="utf-8")
        print(f"OK: disabled old active flights panel in {css_path}")
