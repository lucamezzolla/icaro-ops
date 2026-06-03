-- Icaro Ops West Africa airport patch.
-- Run from the project root:
--
--   sudo mysql icaro_ops < db/mysql/999_apply_west_africa_airports_patch.sql

SOURCE db/mysql/049_create_airport_runway_source_notes_if_missing.sql;
SOURCE db/mysql/050_seed_icao_prefixes_west_africa.sql;
SOURCE db/mysql/051_seed_airports_west_africa.sql;
SOURCE db/mysql/052_seed_airport_runway_source_notes_west_africa.sql;
SOURCE db/mysql/053_verify_west_africa_airports.sql;
