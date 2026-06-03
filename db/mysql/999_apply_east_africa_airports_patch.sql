-- Icaro Ops East Africa / Indian Ocean airport patch.
-- Run from the project root:
--
--   sudo mysql icaro_ops < db/mysql/999_apply_east_africa_airports_patch.sql

SOURCE db/mysql/025_seed_icao_prefixes_east_africa.sql;
SOURCE db/mysql/026_seed_airports_east_africa.sql;
SOURCE db/mysql/027_verify_east_africa_airports.sql;
