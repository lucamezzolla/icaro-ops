# Unified filter UI

This patch aligns the Flights filters with the Buy new aircraft market filters.

## Changes

### Flights

- Uses the same visual structure as the aircraft market filters:
  - `<section class="aircraft-market-filter-panel">`
  - `<div class="aircraft-market-filters">`
  - summary line below the filters
- Shows a small statistic:

```text
Showing X of Y flights.
```

- Keeps the Clear button in the same row as the filters.
- Keeps live filtering behavior.
- Keeps the initial table empty until at least one filter is active.
- Airplane placeholder is changed to:

```text
ICAO type code
```

### Buy new aircraft

- Changes the Clear button to match Flights:

```text
🧹 Clear
```

## Apply

From the project root:

```bash
unzip -o /home/luca/Scaricati/icaro-ops-unified-filter-ui-patch.zip
python3 docs/patch_unified_filter_ui.py

node --check src/js/routes.js
node --check src/js/fleet.js
```

Then hard-refresh both Flights and Fleet.

## Rollback

```bash
git restore src/js/routes.js src/js/fleet.js src/css/routes.css
rm -f docs/patch_unified_filter_ui.py docs/UNIFIED_FILTER_UI.md
```

## Commit

```bash
git add src/js/routes.js src/js/fleet.js src/css/routes.css
git add docs/patch_unified_filter_ui.py docs/UNIFIED_FILTER_UI.md
git commit -m "Unify flights and aircraft market filters"
git push origin development
```
