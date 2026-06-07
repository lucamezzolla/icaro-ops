# Map live panel, red route line and Fleet airport fix

## Apply

```bash
cd /home/luca/Documenti/html/icaro-ops
unzip -o /home/luca/Scaricati/icaro-ops-map-live-panel-red-line-and-fleet-airport-fix.zip

python3 docs/patch_flight_layer_use_original_red_line_and_direct_panel.py
python3 docs/patch_left_panel_direct_aircraft_function.py
python3 docs/patch_fleet_airport_inflight_dash.py
```

Refresh:

```text
Ctrl + F5
```

## Fixes

Aircraft click on map:

```text
- uses the original showSelectedFlightPath(flight) already present in flight-layer.js
- restores the red dashed route line
- calls the left-panel live aircraft function directly
- still emits icaro:aircraft-selected as fallback
```

Live aircraft panel:

```text
- should open again immediately when clicking an aircraft marker
```

Fleet table:

```text
- if aircraft status is IN_FLIGHT, Airport column shows "-"
```

## Why the red line disappeared

The previous patch used a generic map variable, but your real map is:

```text
window.icaroOpsMap
```

and `flight-layer.js` already had its own selected-route function:

```text
showSelectedFlightPath(flight)
```

This patch uses that original function again.
