# Clean Flights dialog and remove bad sentence

## Cause

The current `routes.js` has many overlapping migration patches. The Add flight dialog can stop opening when an old function still expects `#serviceType` while the HTML has `#flightType`, or when duplicate controllers conflict.

## Apply

```bash
cd /home/luca/Documenti/html/icaro-ops
unzip -o /home/luca/Scaricati/icaro-ops-flights-dialog-clean-fix-patch.zip

python3 docs/patch_routes_html_clean_flights.py
python3 docs/replace_routes_js_clean.py
```

Then refresh hard:

```text
Ctrl + F5
```

## Changes

- Removes the text: `A flight is not a flight...`
- `Add flight` opens the dialog again.
- `Flight type` uses a single id: `serviceType`.
- `Scheduled` enables `Scheduled departure UTC`.
- `On demand` clears and disables the time.
- The Routes page JS is replaced by one clean controller, avoiding accumulated conflicting patches.
