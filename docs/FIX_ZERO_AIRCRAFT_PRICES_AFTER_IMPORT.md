# Fix zero aircraft prices after catalog import

## Problem

The full catalog import worked:

```text
301 total aircraft models
292 from aircrafts.ods
9 pre-existing curated models
```

But some pre-existing models had:

```text
new_purchase_price = 0.00
```

Examples seen in the Fleet price order:

```text
CONCORDE
EMB120ER_BRASILIA
SAAB_340B
```

Because Fleet is sorted by price ascending, these appeared first as free aircraft.

## Apply

```bash
cd /home/luca/Documenti/html/icaro-ops
unzip -o /home/luca/Scaricati/icaro-ops-fix-zero-aircraft-prices-patch.zip

sudo mysql icaro_ops < db/mysql/114_fix_zero_aircraft_prices_after_catalog_import.sql
```

## What it does

Only aircraft with missing or zero price are changed.

```text
new_purchase_price <= 0 -> estimated valid price
base_purchase_price <= 0 -> new_purchase_price
used price min/max <= 0 -> derived from new price
lease price <= 0 -> derived from new price
```

Existing valid prices are preserved.

## Verify

```bash
sudo mysql icaro_ops -e "
SELECT COUNT(*) AS zero_or_missing_price_remaining
FROM aircraft_models
WHERE new_purchase_price IS NULL
   OR new_purchase_price <= 0;
"
```

Expected:

```text
0
```

Then check market ordering:

```bash
sudo mysql icaro_ops -e "
SELECT
  model_code,
  icao_type_code,
  manufacturer,
  model_name,
  passenger_capacity_standard,
  new_purchase_price
FROM aircraft_models
ORDER BY new_purchase_price ASC, model_code ASC
LIMIT 40;
"
```

## Commit note

Do not commit failed migrations 108-112.

Commit:

```text
113_import_aircraft_catalog_complete_schema.sql
114_fix_zero_aircraft_prices_after_catalog_import.sql
Fleet JS sorting changes
related docs
```
