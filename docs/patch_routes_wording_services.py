#!/usr/bin/env python3
from pathlib import Path

path = Path("routes.html")
text = path.read_text(encoding="utf-8")

text = text.replace(">Routes<", ">Services<")
text = text.replace("Routes</title>", "Services</title>")
text = text.replace("<span>Routes</span>", "<span>Services</span>")
text = text.replace("<h1>Routes</h1>", "<h1>Services</h1>")
text = text.replace("Add route", "Add service")
text = text.replace("Scheduled routes", "Scheduled services")

path.write_text(text, encoding="utf-8")
print("OK: routes.html wording now says Services.")
