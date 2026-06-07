# Buy aircraft market filters

## Apply

```bash
cd /home/luca/Documenti/html/icaro-ops
unzip -o /home/luca/Scaricati/icaro-ops-buy-aircraft-market-filters-patch.zip

python3 docs/patch_buy_aircraft_market_filters.py
cat docs/aircraft_market_filters_css_append.css >> src/css/fleet.css
```

Refresh:

```text
Ctrl + F5
```

## Changes

Removes these texts from the Buy aircraft area:

```text
Pilot coverage rule
Development open aircraft market
development market/progression explanations
```

Adds filters above the aircraft market table:

```text
ICAO
Search
Max price
Min pax
Max pax
Family
Engine
```

## Important behavior

The aircraft table is empty when no filter is active.

This is intentional, because the catalog is now large and should be searched instead of displayed fully every time.

## Suggested use

Examples:

```text
ICAO = C208
Search = Cessna
Max price = 5000000
Min pax = 8
Family = Fixed wing
Engine = Turboprop
```

## Commit

```bash
git add \
  src/js/aircraft-market-filters.js \
  src/js/fleet-market-table-dialog.js \
  src/js/fleet.js \
  fleet.html \
  src/css/fleet.css \
  docs/patch_buy_aircraft_market_filters.py \
  docs/aircraft_market_filters_css_append.css \
  docs/BUY_AIRCRAFT_MARKET_FILTERS.md

git commit -m "Add filters to aircraft market"
git push
```
