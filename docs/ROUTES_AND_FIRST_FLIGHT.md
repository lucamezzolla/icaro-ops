# Routes and first scheduled flight

This patch adds the first route/flight simulation.

## Apply

```bash
cd /home/luca/Documenti/html/icaro-ops
unzip -o /home/luca/Scaricati/icaro-ops-routes-flights-patch.zip
sudo mysql icaro_ops < db/mysql/075_create_routes_and_flights.sql
```

## Add Routes navigation

```bash
python3 - <<'PY'
from pathlib import Path

for filename in ["index.html", "fleet.html", "staff.html"]:
    path = Path(filename)
    if not path.exists():
        continue
    text = path.read_text(encoding="utf-8")
    if 'href="routes.html"' not in text:
        text = text.replace('<a href="#">Finance</a>', '<a href="routes.html">Routes</a>\\n          <a href="#">Finance</a>', 1)
        text = text.replace('<a href="#">Offers</a>', '<a href="routes.html">Routes</a>\\n          <a href="#">Offers</a>', 1)
        path.write_text(text, encoding="utf-8")
        print(f"OK: added Routes nav to {filename}")
    else:
        print(f"SKIP: Routes nav already present in {filename}")
PY
```

## Optional: show active aircraft on the map

`src/js/flight-layer.js` is included, but it needs access to the Leaflet map.

Patch `src/js/dashboard-map.js`:

```bash
python3 - <<'PY'
from pathlib import Path

path = Path("src/js/dashboard-map.js")
text = path.read_text(encoding="utf-8")

if "window.icaroOpsMap = map;" not in text:
    text = text.replace(
        "fitWorldSafely();",
        "window.icaroOpsMap = map;\\n\\n  fitWorldSafely();",
        1
    )
    path.write_text(text, encoding="utf-8")
    print("OK: exposed map as window.icaroOpsMap")
else:
    print("SKIP: map already exposed")
PY
```

Then add the flight layer script after dashboard-map.js in `index.html`:

```bash
python3 - <<'PY'
from pathlib import Path

path = Path("index.html")
text = path.read_text(encoding="utf-8")

if 'src/js/flight-layer.js' not in text:
    text = text.replace(
        '<script src="src/js/dashboard-map.js"></script>',
        '<script src="src/js/dashboard-map.js"></script>\\n  <script src="src/js/flight-layer.js"></script>'
    )
    path.write_text(text, encoding="utf-8")
    print("OK: added flight layer to index.html")
else:
    print("SKIP: flight layer already present")
PY
```

## Use

Open:

```text
http://127.0.0.1:8080/routes.html
```

Create:

```text
LIRA -> LIML
10:00 UTC
```

Then click:

```text
Start test flight now
```

The system simulates passengers, revenue, fuel cost, maintenance cost, staff cost and profit.

Open the map:

```text
http://127.0.0.1:8080/index.html
```

An aircraft marker should appear while the flight is active.

## Important

For the first Cessna passenger route, you need:

```text
2 active pilots with CPL + C208_TYPE
1 active technician with C208_MAINT
1 available Cessna 208B at LIRA
```

The route uses aircraft DB values such as:

```text
passenger_capacity_standard
cruise_speed_kmh
range_km
fuel_burn_kg_per_hour
maintenance_cost_per_hour
```
