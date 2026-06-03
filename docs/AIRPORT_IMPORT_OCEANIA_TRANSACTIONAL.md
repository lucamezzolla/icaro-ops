# Oceania airport transactional import

Generated from `tmp/oceania_airports_review.csv`.

## Input review status

- Review rows: 1412
- Usable rows from review: 1223
- Unique usable airport codes imported into SQL: 1166
- Duplicate usable-code rows skipped: 57
- Rows with parsed coordinates: 207

## Expected count

If the current DB is at 6931 airports, after a successful Oceania import the theoretical maximum is:

```text
6931 + 1166 = 8097
```

The final total may be lower if some ICAO codes already exist and are updated via `ON DUPLICATE KEY UPDATE`.

## Import file

```text
db/mysql/060_import_oceania_airports_transactional.sql
```

## Rollback behavior

The SQL file uses:

```sql
START TRANSACTION;
...
COMMIT;
```

Preflight checks:
- missing country names in `countries` with `world_region_code = 'OCEANIA'`
- missing ICAO prefixes after prefix insertion

If a preflight check finds a problem, the SQL intentionally triggers a NOT NULL error before inserting airports.

## Apply

```bash
cd /home/luca/Documenti/html/icaro-ops
sudo mysql icaro_ops < db/mysql/060_import_oceania_airports_transactional.sql
```

If it stops at missing countries, copy the `country_name rows_waiting` output and adjust mappings.
