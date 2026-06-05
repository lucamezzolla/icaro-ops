#!/usr/bin/env python3
from pathlib import Path

path = Path("routes.html")
text = path.read_text(encoding="utf-8")

text = text.replace("<title>Icaro Ops - Routes</title>", "<title>Icaro Ops - Services</title>")
text = text.replace("<span>Routes</span>", "<span>Services</span>")
text = text.replace("<h2>Routes</h2>", "<h2>Services</h2>")
text = text.replace("Scheduled daily routes. A route is a commercial promise: aircraft, pilots and timing must support it.", "Scheduled services are commercial offers over abstract air routes. Real flights are generated later and dispatched with compatible aircraft.")
text = text.replace("<h1>Routes</h1>", "<h1>Services over Air Routes</h1>")
text = text.replace("Manage scheduled routes with compact tables and detailed dialogs.", "Manage scheduled services separately from abstract routes and real flight instances.")
text = text.replace('id="addRouteButton" type="button">Add route', 'id="addRouteButton" type="button">Add service')
text = text.replace("<h2>Scheduled routes</h2>", "<h2>Scheduled services</h2>")
text = text.replace("Essential data only. Open details for the full operational view.", "A service is not a flight. Details show air route, service policy and generated flight instances.")
text = text.replace("<th>Route</th>", "<th>Service / Air route</th>")
text = text.replace("<th>Aircraft</th>", "<th>Required class</th>")
text = text.replace("<th>Crew</th>", "<th>Preferred model</th>")
text = text.replace("<th>Duration</th>", "<th>Ticket</th>")
text = text.replace("<th>Ticket</th>", "<th>Status</th>", 1)

text = text.replace("<h2 id=\"routeDialogTitle\">Add route</h2>", "<h2 id=\"routeDialogTitle\">Add scheduled service</h2>")
text = text.replace("<h3>Economic preview</h3>", "<h3>Service economic preview</h3>")
text = text.replace("<h2 id=\"routeDetailTitle\">Route</h2>", "<h2 id=\"routeDetailTitle\">Scheduled service</h2>")

path.write_text(text, encoding="utf-8")
print("OK: routes.html wording now separates services/routes/flights.")
