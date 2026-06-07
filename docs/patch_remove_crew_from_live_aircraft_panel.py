#!/usr/bin/env python3
from pathlib import Path
import re

path = Path("src/js/map-aircraft-left-panel.js")

if not path.exists():
    raise SystemExit("src/js/map-aircraft-left-panel.js not found")

text = path.read_text(encoding="utf-8")

# Remove Pilot rows from the Live aircraft left panel.
text = re.sub(
    r'\n\s*\$\{row\("Pilot 1",[^\n]+\}\s*',
    "\n",
    text
)
text = re.sub(
    r'\n\s*\$\{row\("Pilot 2",[^\n]+\}\s*',
    "\n",
    text
)
text = re.sub(
    r'\n\s*\$\{row\("Crew",[^\n]+\}\s*',
    "\n",
    text
)

# If a previous patch added cleanText only for pilots, it can remain harmless.
path.write_text(text, encoding="utf-8")
print("OK: removed pilot/crew rows from Live aircraft panel.")
