-- Icaro Ops Réunion, Rwanda and Seychelles airport patch.
-- Run from the project root:
--
--   sudo mysql icaro_ops < db/mysql/999_apply_reunion_rwanda_seychelles_airports_patch.sql

SOURCE db/mysql/028_seed_icao_prefixes_reunion_rwanda_seychelles.sql;
SOURCE db/mysql/029_seed_airports_reunion_rwanda_seychelles.sql;
SOURCE db/mysql/030_verify_reunion_rwanda_seychelles_airports.sql;
