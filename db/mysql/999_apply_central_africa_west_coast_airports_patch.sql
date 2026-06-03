-- Icaro Ops Central Africa west/coast airport patch.
-- Run from the project root:
--
--   sudo mysql icaro_ops < db/mysql/999_apply_central_africa_west_coast_airports_patch.sql

SOURCE db/mysql/041_seed_icao_prefixes_central_africa_west_coast.sql;
SOURCE db/mysql/042_seed_airports_central_africa_west_coast.sql;
SOURCE db/mysql/043_verify_central_africa_west_coast_airports.sql;
