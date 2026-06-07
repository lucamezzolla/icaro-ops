# ATR development test unlock

## Apply

```bash
cd /home/luca/Documenti/html/icaro-ops
unzip -o /home/luca/Scaricati/icaro-ops-atr-test-unlock-patch.zip

sudo mysql icaro_ops < db/mysql/098_dev_budget_and_atr_test_unlock.sql
python3 docs/patch_fleet_catalog_show_atr_test.py
```

Then refresh:

```text
Ctrl + F5
```

## What this does

Development-only test script:

```text
- adds 20,000,000 EUR to company id 1
- makes ATR42_600 active and available new
- grants ATR42_TYPE to up to 4 active pilots
```

Catalog patch:

```text
- shows C208 and ATR42_600 in Fleet → Buy new aircraft
- calculates pilot coverage per model:
  C208 -> C208_TYPE
  ATR42_600 -> ATR42_TYPE
```

## Why you may not see ATR now

Your current Fleet catalog is hardcoded to show only:

```text
C208B_GRAND_CARAVAN_EX
```

So even if ATR exists in `aircraft_models`, it is hidden from the buy dialog.

## Pilot requirement

Your current purchase rule says:

```text
each operational aircraft requires 2 active qualified pilots
```

If you already have 1 C208 and want to buy a second aircraft, the purchase requires:

```text
4 pilots qualified for the target aircraft type
```

For ATR this means:

```text
4 pilots with CPL + ATR42_TYPE
```

The dev SQL grants that rating for testing.
