# Europe airport transactional import

This package was generated from `tmp/europe_airports_review.csv`.

## Input review status

- Review rows: 3666
- Usable rows from review: 3102
- Unique usable airport codes imported into SQL: 2738
- Duplicate usable-code rows skipped: 364
- Rows with parsed coordinates: 433

## Expected count

If the current DB is at 3660 airports, after a successful Europe import:

```text
3660 + 2738 = 6398
```

This is a theoretical count. Some ICAO codes may already exist from the Asia import, especially Russia, Turkey, Cyprus, Armenia, Azerbaijan and Georgia. Since the SQL uses `ON DUPLICATE KEY UPDATE`, the final total may be lower if overlapping ICAO codes are updated instead of inserted.

## Import file

```text
db/mysql/058_import_europe_airports_transactional.sql
```

## Rollback behavior

The SQL file uses:

```sql
START TRANSACTION;
...
COMMIT;
```

Preflight checks:
- missing country names in `countries` with `world_region_code = 'EUROPE'`
- missing ICAO prefixes after prefix insertion

If a preflight check finds a problem, the SQL intentionally triggers a NOT NULL error before inserting airports.

## Apply

```bash
cd /home/luca/Documenti/html/icaro-ops
sudo mysql icaro_ops < db/mysql/058_import_europe_airports_transactional.sql
```

If it stops at missing countries, copy the `country_name rows_waiting` output and adjust country-name mappings.
