# Full aircraft catalog import and Fleet price sort

Rows in uploaded ODS: 321
Rows imported after cleanup: 292
Rows skipped: 29

Design rule:

```text
All aircraft are visible from registration.
The only purchase blocker is company budget.
```

Apply:

```bash
cd /home/luca/Documenti/html/icaro-ops
unzip -o /home/luca/Scaricati/icaro-ops-full-aircraft-catalog-and-price-sort-patch.zip

sudo mysql icaro_ops < db/mysql/108_import_aircraft_catalog_from_ods.sql
python3 docs/patch_fleet_aircraft_price_sort.py
```

Refresh:

```text
Ctrl + F5
```

The ODS does not contain prices, so missing aircraft get development/gameplay prices estimated from category and passenger capacity. Existing prices are preserved unless NULL or 0.

Fleet market/catalog is sorted by purchase price ascending in JS.
