#!/usr/bin/env python3
from pathlib import Path

path = Path("routes.html")
text = path.read_text(encoding="utf-8")

text = text.replace("<th>Preferred models</th>", "<th>Airplanes</th>")
text = text.replace("<th>Preferred model</th>", "<th>Airplanes</th>")
text = text.replace("Preferred models", "Airplanes")
text = text.replace("Preferred model", "Airplanes")

path.write_text(text, encoding="utf-8")
print("OK: routes.html renamed Preferred models to Airplanes.")
