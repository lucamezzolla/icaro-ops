# North America airport transactional import

Generated from `tmp/north_america_airports_review.csv`.

## Input review status

- Review rows: 1699
- Usable rows from review: 1431
- Unique usable airport codes imported into SQL: 979
- Duplicate usable-code rows skipped: 452
- Rows with parsed coordinates: 192

## Expected count

If the current DB is at 5955 airports, after a successful North America import the theoretical maximum is:

```text
5955 + 979 = 6934
```

The final total may be lower if some ICAO codes already exist and are updated via `ON DUPLICATE KEY UPDATE`.

## Import file

```text
db/mysql/059_import_north_america_airports_transactional.sql
```

## Rollback behavior

The SQL file uses:

```sql
START TRANSACTION;
...
COMMIT;
```

Preflight checks:
- missing country names in `countries` with `world_region_code = 'NORTH_AMERICA'`
- missing ICAO prefixes after prefix insertion

If a preflight check finds a problem, the SQL intentionally triggers a NOT NULL error before inserting airports.

## Apply

```bash
cd /home/luca/Documenti/html/icaro-ops
sudo mysql icaro_ops < db/mysql/059_import_north_america_airports_transactional.sql
```

If it stops at missing countries, copy the `country_name rows_waiting` output and adjust mappings.
