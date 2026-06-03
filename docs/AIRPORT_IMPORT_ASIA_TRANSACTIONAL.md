# Asia airport transactional import

This package was generated from `tmp/asia_airports_review.csv`.

## Input review status

- Review rows: 3133
- Usable rows from review: 2153
- Unique usable airport codes imported into SQL: 2112
- Duplicate usable-code rows skipped: 41

The skipped duplicates are written to:

```text
tmp/asia_airports_review_duplicate_usable_codes.csv
```

The normalized import rows are written to:

```text
tmp/asia_airports_normalized_import_rows.csv
```

## Expected count

If the current DB is at 1548 airports, after a successful Asia import:

```text
1548 + 2112 = 3660
```

## Import file

```text
db/mysql/057_import_asia_airports_transactional.sql
```

## Rollback behavior

The SQL file uses:

```sql
START TRANSACTION;
...
COMMIT;
```

It creates only TEMPORARY tables before persistent inserts.

Preflight checks:
- missing country names in `countries` with `world_region_code = 'ASIA'`
- missing ICAO prefixes after prefix insertion

If a preflight check finds a problem, the SQL intentionally triggers a NOT NULL error before inserts into `airports`.

If it fails before `COMMIT`, the persistent changes are rolled back.

## Apply

```bash
cd /home/luca/Documenti/html/icaro-ops
sudo mysql icaro_ops < db/mysql/057_import_asia_airports_transactional.sql
```

## Verify

```bash
sudo mysql icaro_ops -e "SELECT COUNT(*) AS total_airports FROM airports;"
```

Expected:

```text
3660
```

## Notes

Country-name mismatches are likely the first issue to resolve. If the SQL stops, copy the output of:

```sql
SELECT * FROM tmp_asia_missing_countries;
```

from the terminal output and fix country names or add a mapping before rerunning.
