-- Icaro Ops East / Southern Africa airport patch.
-- Run from the project root:
--
--   sudo mysql icaro_ops < db/mysql/999_apply_east_southern_africa_airports_patch.sql

SOURCE db/mysql/031_create_airport_runway_source_notes_if_missing.sql;
SOURCE db/mysql/032_seed_icao_prefixes_east_southern_africa.sql;
SOURCE db/mysql/033_seed_airports_east_southern_africa.sql;
SOURCE db/mysql/034_seed_airport_runway_source_notes_east_southern_africa.sql;
SOURCE db/mysql/035_verify_east_southern_africa_airports.sql;
