# South America airport transactional import

Generated from `tmp/south_america_airports_review.csv`.

## Input review status

- Review rows: 1482
- Usable rows from review: 1447
- Unique usable airport codes imported into SQL: 1442
- Duplicate usable-code rows skipped: 5
- Rows with parsed coordinates: 359

## Expected count

If the current DB is at 7900 airports, after a successful South America import the theoretical maximum is:

```text
7900 + 1442 = 9342
```

The final total may be lower if some ICAO codes already exist and are updated via `ON DUPLICATE KEY UPDATE`.

## Import file

```text
db/mysql/061_import_south_america_airports_transactional.sql
```

## Rollback behavior

The SQL file uses:

```sql
START TRANSACTION;
...
COMMIT;
```

Preflight checks:
- missing country names in `countries` with `world_region_code = 'SOUTH_AMERICA'`
- missing ICAO prefixes after prefix insertion

If a preflight check finds a problem, the SQL intentionally triggers a NOT NULL error before inserting airports.

## Apply

```bash
cd /home/luca/Documenti/html/icaro-ops
sudo mysql icaro_ops < db/mysql/061_import_south_america_airports_transactional.sql
```

If it stops at missing countries, copy the `country_name rows_waiting` output and adjust mappings.
