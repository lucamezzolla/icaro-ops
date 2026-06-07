# Move live flight data into map popup

## Problem

The previous patch showed speed/timer in Fleet through a floating "Active flights" panel.

That was wrong for the intended UX.

## Correct behavior

Live speed and remaining timer must appear inside the map popup/fumetto when clicking the selected aircraft.

## Apply

```bash
cd /home/luca/Documenti/html/icaro-ops
unzip -o /home/luca/Scaricati/icaro-ops-map-popup-live-flight-fix-patch.zip

python3 docs/remove_generic_active_flight_panels.py
python3 docs/include_map_popup_live_flight_script.py

cat docs/map_popup_live_flight_css_append.css >> src/css/dashboard.css
cat docs/map_popup_live_flight_css_append.css >> src/css/routes.css
cat docs/map_popup_live_flight_css_append.css >> src/css/fleet.css
```

Refresh:

```text
Ctrl + F5
```

## What it does

Removes generic scripts:

```text
src/js/active-flight-clickable-enhancer.js
src/js/active-flight-timer-dialog.js
```

from HTML pages.

Adds:

```text
src/js/map-active-flight-popup.js
```

only to map-like pages:

```text
dashboard.html
map.html
operations.html
index.html
```

## How it works

When you click an aircraft in the map:

```text
1. The existing map popup opens.
2. This script detects the selected aircraft.
3. It calls active-detail.php for that specific aircraft/flight.
4. It injects live data inside the popup.
```

The popup shows:

```text
speed
route
remaining timer
progress
arrival UTC
crew
```

The timer updates every second.

## Important

This patch assumes the map popup is a normal DOM popup, for example Leaflet:

```text
.leaflet-popup-content
```

If your map uses another custom popup class, send me the map JS/HTML and I will add the exact selector.
