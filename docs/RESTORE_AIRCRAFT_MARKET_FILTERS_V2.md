# Restore aircraft market filters v2

This version is more robust if `openCatalogModelDetail` is missing or was renamed.

## Apply

From the project root:

```bash
unzip -o /home/luca/Scaricati/icaro-ops-restore-aircraft-market-filters-patch-v2.zip
python3 docs/patch_restore_aircraft_market_filters_v2.py
```

Then hard-refresh the browser page.

## Commit

```bash
git add src/js/fleet.js src/css/fleet.css docs/patch_restore_aircraft_market_filters_v2.py docs/RESTORE_AIRCRAFT_MARKET_FILTERS_V2.md
git commit -m "Restore aircraft market filters"
git push origin development
```
