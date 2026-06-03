-- Icaro Ops Southern Africa airport patch.
-- Run from the project root:
--
--   sudo mysql icaro_ops < db/mysql/999_apply_southern_africa_airports_patch.sql

SOURCE db/mysql/044_create_airport_runway_source_notes_if_missing.sql;
SOURCE db/mysql/045_seed_icao_prefixes_southern_africa.sql;
SOURCE db/mysql/046_seed_airports_southern_africa.sql;
SOURCE db/mysql/047_seed_airport_runway_source_notes_southern_africa.sql;
SOURCE db/mysql/048_verify_southern_africa_airports.sql;
