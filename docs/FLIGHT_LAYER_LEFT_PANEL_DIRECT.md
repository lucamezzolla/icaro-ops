# Flight layer direct left-panel patch

## Problem

The real aircraft markers are created in:

```text
src/js/flight-layer.js
```

That file still used:

```text
marker.bindPopup(...)
```

and handled click locally. So the new left-panel script could not reliably know which aircraft was clicked.

## Apply

```bash
cd /home/luca/Documenti/html/icaro-ops
unzip -o /home/luca/Scaricati/icaro-ops-flight-layer-left-panel-direct-patch.zip

python3 docs/patch_flight_layer_direct_left_panel.py
python3 docs/patch_left_panel_listen_aircraft_event.py
```

Refresh:

```text
Ctrl + F5
```

## What changes

Aircraft markers:

```text
- no longer open the Leaflet aircraft popup
- emit a custom event: icaro:aircraft-selected
- include aircraftId and flightInstanceId
```

Left panel:

```text
- listens for icaro:aircraft-selected
- loads active-detail.php for that exact flight instance
- replaces the Company/base panel with aircraft live status
```

Base markers:

```text
- still restore Company/base data when clicked
```

## If it still does not select the correct left panel

Run:

```bash
grep -n "id=.*sidebar\|id=.*Panel\|class=.*sidebar\|class=.*panel" index.html
```

and send me the output.
