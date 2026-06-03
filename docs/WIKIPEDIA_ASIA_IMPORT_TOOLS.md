# Icaro Ops Wikipedia Asia airport import tools

These are exploratory tools for the Asia airport import.

They do not generate SQL yet. First they create review CSV files so we can verify
that we are reading the correct Wikipedia list pages.

## Step 1: fetch Asia airport list links

```bash
cd /home/luca/Documenti/html/icaro-ops
python3 tools/importers/fetch_wikipedia_airport_list_links.py \
  --out tmp/wiki_airport_lists_asia.csv
```

This creates:

```text
tmp/wiki_airport_lists_asia.csv
```

## Step 2: inspect linked pages

```bash
python3 tools/importers/probe_wikipedia_airport_tables.py \
  --in tmp/wiki_airport_lists_asia.csv \
  --out tmp/wiki_airport_lists_asia_probe.csv
```

This creates:

```text
tmp/wiki_airport_lists_asia_probe.csv
```

## Why this step exists

The Wikipedia country pages are not perfectly uniform. Some have clean airport
tables, some have multiple tables, some have no ICAO for some rows, and some use
different column names.

After reviewing the two CSV files, the next step is to create the real parser
that generates:

```text
tmp/asia_airports_review.csv
db/mysql/057_seed_airports_asia_generated.sql
docs/AIRPORT_IMPORT_ASIA.md
```
