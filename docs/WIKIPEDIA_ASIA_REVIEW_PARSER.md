# Asia airport review parser

This package adds a review parser. It does **not** generate SQL yet.

## Current status from supplied probe files

The Asia index extraction found 61 links and all probed pages returned status `ok`.

Important observations:

- Some links are not part of the Asia import pass, such as Antarctica and Egypt.
- Some links may be duplicates or politically separate pages, such as Palestine / State of Palestine.
- Several pages have multiple wikitables, especially India, Bangladesh, Israel, Philippines, Vietnam, Armenia and others.

## Run

```bash
cd /home/luca/Documenti/html/icaro-ops
python3 tools/importers/build_asia_airports_review.py \
  --links tmp/wiki_airport_lists_asia.csv \
  --out tmp/asia_airports_review.csv
```

Generated files:

```text
tmp/asia_airports_review.csv
tmp/asia_airports_review_summary.csv
```

## Review

Useful commands:

```bash
wc -l tmp/asia_airports_review.csv
wc -l tmp/asia_airports_review_summary.csv

column -s, -t tmp/asia_airports_review_summary.csv | less -S

grep -n ",missing_usable_4_char_code$" tmp/asia_airports_review.csv | head -50
```

## Why review first?

The final SQL must be one transactional import file:

```sql
START TRANSACTION;
-- temp tables
-- preflight checks with SIGNAL SQLSTATE '45000'
-- insert prefixes
-- insert airports
-- insert runway notes
COMMIT;
```

If an error occurs before `COMMIT`, the import rolls back and does not dirty the DB.
