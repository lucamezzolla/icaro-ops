-- Icaro Ops East Africa / Indian Ocean airport patch.
-- Run from the project root:
--
--   sudo mysql icaro_ops < db/mysql/999_apply_east_africa_small_airports_patch.sql

SOURCE db/mysql/020_create_airport_runways.sql;
SOURCE db/mysql/021_seed_icao_prefixes_east_africa_small.sql;
SOURCE db/mysql/022_seed_airports_east_africa_small.sql;
SOURCE db/mysql/023_seed_airport_runway_source_notes_burundi.sql;
SOURCE db/mysql/024_verify_east_africa_small_airports.sql;
