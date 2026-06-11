# Flights live filters

This patch improves the Flights filters.

## Changes

- Text filters now apply immediately while typing.
- The Scheduled combo applies immediately when changed.
- The Apply filters button is removed.
- The Clear button is placed inline with the filters.
- The Clear button now has a small icon:

```text
🧹 Clear
```

The table still starts empty. It is populated only when at least one filter has a value.

## Apply

From the project root:

```bash
unzip -o /home/luca/Scaricati/icaro-ops-flights-live-filters-patch.zip
python3 docs/patch_flights_live_filters.py

node --check src/js/routes.js
```

Then hard-refresh the Flights page.

## Rollback

```bash
git restore src/js/routes.js
rm -f docs/patch_flights_live_filters.py docs/FLIGHTS_LIVE_FILTERS.md
```

## Commit

```bash
git add src/js/routes.js docs/patch_flights_live_filters.py docs/FLIGHTS_LIVE_FILTERS.md
git commit -m "Improve flights live filters"
git push origin development
```
