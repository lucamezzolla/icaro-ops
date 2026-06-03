# Icaro Ops Database v1

This is the first MySQL/MariaDB database structure for Icaro Ops.

## Language rule

Database content must stay in English.

The game interface is multilingual, but translations must live in the i18n layer, not in database rows.

## Main tables

- `icao_regions`
- `icao_prefixes`
- `airports`
- `airport_game_profiles`
- `airlines`

## Why airport data is split

`airports` contains descriptive real-world airport data.

`airport_game_profiles` contains game balancing values such as:

- starter base availability
- airport size
- slot cost level
- demand levels
- maximum aircraft class

This makes it possible to import many real airports while controlling which ones are suitable for a novice airline manager.

## Install locally

From the project root:

```bash
mysql -u root -p < db/mysql/999_create_all.sql
```

If `SOURCE` paths do not resolve on your system, run files one by one in numeric order:

```bash
mysql -u root -p < db/mysql/000_create_database.sql
mysql -u root -p < db/mysql/001_create_icao_regions.sql
mysql -u root -p < db/mysql/002_create_icao_prefixes.sql
mysql -u root -p < db/mysql/003_create_airports.sql
mysql -u root -p < db/mysql/004_create_airport_game_profiles.sql
mysql -u root -p < db/mysql/005_create_airlines.sql
mysql -u root -p < db/mysql/006_seed_icao_regions.sql
mysql -u root -p < db/mysql/007_seed_icao_prefixes.sql
mysql -u root -p < db/mysql/008_seed_starter_airports.sql
mysql -u root -p < db/mysql/009_seed_airport_game_profiles.sql
mysql -u root -p < db/mysql/010_views_base_selection.sql
```

## Useful checks

```sql
USE icaro_ops;

SELECT * FROM v_base_selection_regions ORDER BY region_code;

SELECT
  region_code,
  prefix,
  icao_code,
  airport_name,
  city,
  country_name,
  starter_difficulty,
  max_aircraft_class
FROM v_base_selection_airports
ORDER BY region_code, country_name, city;
```

## Next step

The next database step is to expand `icao_prefixes` and import a larger worldwide airport dataset.

The first UI step is to make the setup flow use:

1. region
2. ICAO prefix / country
3. starter airport
