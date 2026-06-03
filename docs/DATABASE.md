# Icaro Ops Database v2

This version changes the initial base selection model.

## User-facing base selection flow

```text
World region
→ Country / territory
→ Airport
```

## Important rule

ICAO remains primary for airports.

The `airports` table uses:

```sql
icao_code CHAR(4) PRIMARY KEY
```

This means future game references to an airport should use the ICAO code whenever possible.

## Current data included

This version includes:

- world regions
- countries / territories grouped by region
- empty `icao_prefixes`
- empty `airports`
- empty `airport_game_profiles`

Airports are intentionally empty because the long airport list will be added later.

## Main tables

- `world_regions`
- `countries`
- `icao_prefixes`
- `airports`
- `airport_game_profiles`
- `airlines`

## Useful views

- `v_base_selection_regions`
- `v_base_selection_countries`
- `v_base_selection_airports`

Since airports are empty for now, airport counts will be zero until the airport import is added.

## Install locally

From the project root:

```bash
mysql -u root -p < db/mysql/999_create_all.sql
```

If you use MariaDB with sudo:

```bash
sudo mysql < db/mysql/999_create_all.sql
```

## Reset local database

During early development, the simplest reset is:

```bash
sudo mysql -e "DROP DATABASE IF EXISTS icaro_ops;"
sudo mysql < db/mysql/999_create_all.sql
```

## Checks

```sql
USE icaro_ops;

SELECT * FROM v_base_selection_regions ORDER BY region_name;

SELECT
  region_name,
  subregion_name,
  country_name,
  airport_count
FROM v_base_selection_countries
ORDER BY region_name, subregion_name, country_name;

SELECT COUNT(*) FROM airports;
```

Expected airport count for this version:

```text
0
```
