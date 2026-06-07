# Aircraft market cleanup, Details fix and generated images

## Apply

```bash
cd /home/luca/Documenti/html/icaro-ops
unzip -o /home/luca/Scaricati/icaro-ops-aircraft-market-cleanup-details-images-patch.zip

python3 docs/patch_aircraft_market_cleanup_details.py
cat docs/aircraft_market_cleanup_css_append.css >> src/css/fleet.css

sudo mysql icaro_ops < db/mysql/115_assign_generated_aircraft_images.sql
```

Refresh:

```text
Ctrl + F5
```

## Changes

```text
- removes BUY RULE from the Buy aircraft market
- keeps backend budget validation untouched
- fixes Details button id resolution
- assigns generated SVG images only to aircraft without image_asset_path
```

## About BUY RULE

The column is UI-only. The meaningful purchase rule remains:

```text
purchase requires enough company budget
```

## Generated images

```text
src/img/aircraft/generated/fixed-wing.svg
src/img/aircraft/generated/turboprop.svg
src/img/aircraft/generated/jet.svg
src/img/aircraft/generated/helicopter.svg
src/img/aircraft/generated/concorde.svg
```

Existing custom images are preserved.
