# Map auto-dispatch refresh v6

This patch fixes the behavior where a due scheduled flight starts only after leaving and returning to the map.

## Cause

The automatic scheduled-service dispatcher was called by the Flights/Routes page, but the map active-flight API only completed existing flights and listed already-active flights.

So if the player stayed on the map while a scheduled departure became due, the map polling did not start the due scheduled service.

## Fix

- Adds a shared backend dispatcher:
  - `api/lib/scheduled-service-dispatcher.php`
- Makes `api/public/dispatch/process-due-routes.php` use that shared dispatcher.
- Makes `api/public/flights/active.php` run due scheduled-service dispatch before returning active flights.
- Reduces map active-flight polling from 15 seconds to 5 seconds.
- Refreshes active flights when the browser tab/window regains focus.

## Apply

From the project root:

```bash
unzip -o /home/luca/Scaricati/icaro-ops-map-autodispatch-refresh-patch-v6.zip
python3 docs/patch_map_autodispatch_refresh_v6.py

php -l api/lib/scheduled-service-dispatcher.php
php -l api/public/dispatch/process-due-routes.php
php -l api/public/flights/active.php
node --check src/js/flight-layer.js
node --check src/js/routes.js
```

Then create a scheduled flight a few minutes in the future, stay on the map, and wait.

Expected behavior:

```text
21:12 UTC, flight 21:14 UTC => not visible yet
21:14 UTC / within ~5 seconds => aircraft appears on map
```

## Rollback

```bash
git restore api/public/dispatch/process-due-routes.php api/public/flights/active.php src/js/flight-layer.js
rm -f api/lib/scheduled-service-dispatcher.php
rm -f docs/patch_map_autodispatch_refresh_v6.py docs/MAP_AUTODISPATCH_REFRESH_V6.md
```

## Commit

```bash
git add api/lib/scheduled-service-dispatcher.php api/public/dispatch/process-due-routes.php api/public/flights/active.php src/js/flight-layer.js docs/patch_map_autodispatch_refresh_v6.py docs/MAP_AUTODISPATCH_REFRESH_V6.md
git commit -m "Refresh map auto-dispatch for scheduled flights"
git push origin development
```
