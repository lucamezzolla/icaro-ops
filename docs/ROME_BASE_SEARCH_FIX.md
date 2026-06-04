# Rome base and airport search fix

This patch fixes two problems:

1. Search for `LIRA` was returning fuzzy matches such as Lira, Uganda.
2. Ciampino/LIRA could not be found or displayed because Italy airport rows imported from Wikipedia currently have many missing coordinates.

## Files

```text
api/public/airports/search.php
api/public/company/current.php
db/mysql/064_fix_rome_base_airport_coordinates.sql
docs/ROME_BASE_SEARCH_FIX.md
```

## Apply

```bash
cd /home/luca/Documenti/html/icaro-ops
unzip -o /home/luca/Scaricati/icaro-ops-rome-base-search-fix-patch.zip
sudo mysql icaro_ops < db/mysql/064_fix_rome_base_airport_coordinates.sql
```

## Test

```bash
curl "http://127.0.0.1:8080/api/public/airports/search.php?q=LIRA"
curl "http://127.0.0.1:8080/api/public/airports/search.php?q=Ciampino"
```

Expected: `LIRA` should return Rome Ciampino exactly, not fuzzy matches.

For company:

```bash
sudo mysql icaro_ops -e "SELECT id, company_name, base_airport_icao_code FROM companies;"
curl "http://127.0.0.1:8080/api/public/company/current.php?companyId=REAL_ID"
```
