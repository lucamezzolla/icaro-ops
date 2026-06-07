# Aircraft catalog complete schema import

## Why this replaces 108-112

The previous migrations discovered required columns one by one:

```text
108 failed: iata_type_code
109 failed: aircraft_family
110 failed: operation_role
111 failed: engine_type
112 failed: engine_count
```

This migration was generated after reading the real schema:

```text
DESCRIBE aircraft_models;
```

So it includes all required NOT NULL fields.

## Apply

Do not rerun `108`, `109`, `110`, `111` or `112`.

Run:

```bash
cd /home/luca/Documenti/html/icaro-ops
unzip -o /home/luca/Scaricati/icaro-ops-aircraft-catalog-complete-schema-patch.zip

sudo mysql icaro_ops < db/mysql/113_import_aircraft_catalog_complete_schema.sql
```

The Fleet JS price sorting patch was already applied successfully, so you do not need to run it again.

## Import summary

Rows imported from `aircrafts.ods`:

```text
292
```

Rows skipped:

```text
29
```

Skipped rows include invalid, zero-pax, duplicate and fictional/test entries.

## Gameplay design

```text
No aircraft progression lock.
All aircraft visible from registration.
Budget is the only purchase blocker.
```

## Data quality

The ODS contains only:

```text
name
IATA
ICAO
category
max passengers
```

So fields like prices, weight, runway, ceiling, fuel and maintenance are gameplay estimates.

They are marked as:

```text
data_quality = PARTIAL
data_source_name = aircrafts.ods
data_source_url = local:aircrafts.ods
```

## Verify

```bash
sudo mysql icaro_ops -e "
SELECT
  model_code,
  aircraft_family,
  operation_role,
  engine_type,
  engine_count,
  crew_required_min,
  iata_type_code,
  icao_type_code,
  manufacturer,
  model_name,
  passenger_capacity_standard,
  new_purchase_price
FROM aircraft_models
ORDER BY new_purchase_price ASC, model_code ASC
LIMIT 30;
"
```

## Commit

Only commit the successful complete migration, plus the already successful Fleet JS sort patch.

```bash
git add \
  db/mysql/113_import_aircraft_catalog_complete_schema.sql \
  docs/AIRCRAFT_CATALOG_COMPLETE_SCHEMA.md \
  src/js/fleet-market-table-dialog.js \
  src/js/fleet.js \
  docs/patch_fleet_aircraft_price_sort_fix.py \
  docs/AIRCRAFT_CATALOG_IMPORT_FIX.md

git commit -m "Import full aircraft catalog with complete schema"
git push
```
