#!/usr/bin/env python3
from pathlib import Path
import re

path = Path("routes.html")
text = path.read_text(encoding="utf-8")

text = re.sub(
    r'<input([^>]*id="scheduledTime"[^>]*)>',
    lambda m: (
        "<input" +
        re.sub(r'\stype="[^"]*"', '', m.group(1)) +
        ' type="time">'
    ),
    text,
    count=1
)

if 'id="scheduledTime"' not in text:
    raise SystemExit("scheduledTime input not found in routes.html")

path.write_text(text, encoding="utf-8")
print("OK: scheduledTime input normalized as type=time")
