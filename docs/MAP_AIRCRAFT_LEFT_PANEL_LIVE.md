# Map aircraft left panel live data

## Goal

Remove aircraft popup/fumetto data and show the selected aircraft live data in the left panel, replacing Company data.

Company data comes back when clicking a base.

## Apply

```bash
cd /home/luca/Documenti/html/icaro-ops
unzip -o /home/luca/Scaricati/icaro-ops-map-left-panel-aircraft-live-patch.zip

python3 docs/remove_old_active_flight_popup_scripts.py
python3 docs/include_map_aircraft_left_panel_script.py

cat docs/map_aircraft_left_panel_css_append.css >> src/css/dashboard.css
cat docs/map_aircraft_left_panel_css_append.css >> src/css/routes.css
cat docs/map_aircraft_left_panel_css_append.css >> src/css/fleet.css
```

Refresh:

```text
Ctrl + F5
```

## Behavior

When clicking an aircraft in flight on the map:

```text
- no popup/fumetto should be used for aircraft live data
- the left panel replaces Company data
- it shows data for the selected aircraft
- timer updates every second
```

Shown fields:

```text
registration
aircraft type
flight code
route
status
speed
departure UTC
arrival UTC
remaining timer
progress
passengers
pilots
```

When clicking a base:

```text
Company panel is restored
```

## Important

The script searches for a left panel using these selectors:

```text
#companyPanel
#companyInfoPanel
#companyOverview
#leftPanel
#sidebar
.company-panel
.company-overview
.left-panel
.sidebar
```

If your real Company panel has a different id/class, tell me the HTML snippet and I will bind it exactly.
