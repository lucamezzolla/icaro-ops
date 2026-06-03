-- Icaro Ops Central Africa airport patch, fixed version.
-- Safe to run from 588-airports state.
--
--   sudo mysql icaro_ops < db/mysql/999_apply_central_africa_airports_patch.sql

SOURCE db/mysql/036_create_airport_runway_source_notes_if_missing.sql;
SOURCE db/mysql/037_seed_icao_prefixes_central_africa.sql;
SOURCE db/mysql/038_seed_airports_central_africa.sql;
SOURCE db/mysql/039_seed_airport_runway_source_notes_central_africa_safe.sql;
SOURCE db/mysql/040_verify_central_africa_airports.sql;
