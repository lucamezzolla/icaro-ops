# Remove crew from live aircraft panel and restore red route line

## Why

Pilots are a company pool in the current design. They are not permanently assigned to aircraft and, for now, should not be shown in the selected-aircraft live panel.

The red dashed route line is important and must appear again when clicking an aircraft on the map.

## Apply

```bash
cd /home/luca/Documenti/html/icaro-ops
unzip -o /home/luca/Scaricati/icaro-ops-remove-crew-and-restore-red-route-line-patch.zip

python3 docs/patch_remove_crew_from_live_aircraft_panel.py
python3 docs/patch_restore_red_dashed_route_line.py
```

Refresh:

```text
Ctrl + F5
```

## Changes

Live aircraft left panel:

```text
- removes Pilot 1
- removes Pilot 2
- removes Crew if present
```

Aircraft map click:

```text
- keeps the left-panel aircraft data
- draws the red dashed route line again
```

The line tries several coordinate sources from the flight object:

```text
origin/destination latitude/longitude
departure/arrival latitude/longitude
from/to latitude/longitude
route_points / routePoints / polyline_points / path / coordinates
```

If the line still does not appear, run:

```bash
sed -n '1,140p' src/js/flight-layer.js
```

and send me the output so I can bind to the exact route geometry already used by the map.
