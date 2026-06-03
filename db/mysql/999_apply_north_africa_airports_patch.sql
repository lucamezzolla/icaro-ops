-- Icaro Ops North Africa airport patch.
-- Run from the project root:
--
--   sudo mysql icaro_ops < db/mysql/999_apply_north_africa_airports_patch.sql

SOURCE db/mysql/014_alter_airports_minimal_import_fields.sql;
SOURCE db/mysql/015_create_airport_icao_aliases.sql;
SOURCE db/mysql/016_seed_icao_prefixes_north_africa.sql;
SOURCE db/mysql/017_seed_airports_north_africa.sql;
SOURCE db/mysql/018_seed_airport_icao_aliases_western_sahara.sql;
SOURCE db/mysql/019_verify_north_africa_airports.sql;
