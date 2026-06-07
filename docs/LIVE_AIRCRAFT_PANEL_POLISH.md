# Live aircraft panel polish

## Apply

```bash
cd /home/luca/Documenti/html/icaro-ops
unzip -o /home/luca/Scaricati/icaro-ops-live-aircraft-panel-polish-patch.zip

python3 docs/patch_live_aircraft_panel_polish.py
python3 docs/patch_flight_layer_restore_selected_route_line.py
```

Refresh:

```text
Ctrl + F5
```

## Changes

Live aircraft panel:

```text
- Pilot 1 prints "-" if missing/null
- Pilot 2 prints "-" if missing/null
- removes the "Company" button from the Live aircraft panel
```

Map aircraft click:

```text
- keeps the left-panel live aircraft behavior
- restores the selected red dashed route line
```

## Note

The red dashed line uses the coordinates present in the flight object:

```text
origin_latitude / origin_lat / origin_airport_latitude / departure_latitude
origin_longitude / origin_lng / origin_airport_longitude / departure_longitude
destination_latitude / destination_lat / destination_airport_latitude / arrival_latitude
destination_longitude / destination_lng / destination_airport_longitude / arrival_longitude
```

If the line still does not appear, the active-flight API/flight layer may not currently provide origin/destination coordinates in the object used by `flight-layer.js`; in that case send me the first 120 lines of `src/js/flight-layer.js` and the JSON returned by its API endpoint.
