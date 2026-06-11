# On-demand aircraft dispatch dialog

This patch improves non-scheduled / on-demand flight start behavior.

## Problem

When starting an on-demand flight with multiple compatible aircraft, the UI should not rely on a popup/alert. It should show a proper dialog with the flight data and let the user choose one of the aircraft configured when the flight was created.

The debug file confirmed the current flow in `src/js/routes.js`:
- `startFlightNow()` fetches `available-aircraft.php`
- if multiple aircraft are available it calls `chooseAircraftForOnDemandFlight()`
- after starting the flight it uses a browser `alert(...)`

## Changes

- The manual aircraft selection dialog now shows:
  - Flight code
  - Type
  - Route
  - Compatible ICAO types
  - Configured aircraft models
  - Available aircraft at the origin airport
- Available aircraft listed by the backend are already filtered by the configured compatible model codes.
- The success popup alert is replaced by a proper dialog:
  - Flight code
  - Aircraft
  - Crew
  - Technician
  - Estimated profit
  - Scheduled arrival UTC

## Apply

From the project root:

```bash
unzip -o /home/luca/Scaricati/icaro-ops-ondemand-aircraft-dispatch-dialog-patch.zip
python3 docs/patch_ondemand_aircraft_dispatch_dialog.py

node --check src/js/routes.js
```

Then hard-refresh the Flights page.

## Rollback

```bash
git restore src/js/routes.js src/css/routes.css
rm -f docs/patch_ondemand_aircraft_dispatch_dialog.py docs/ONDEMAND_AIRCRAFT_DISPATCH_DIALOG.md
```

## Commit

```bash
git add src/js/routes.js src/css/routes.css
git add docs/patch_ondemand_aircraft_dispatch_dialog.py docs/ONDEMAND_AIRCRAFT_DISPATCH_DIALOG.md
git commit -m "Improve on-demand aircraft dispatch dialog"
git push origin development
```
