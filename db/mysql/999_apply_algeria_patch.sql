-- Icaro Ops Algeria airport patch.
-- Run from the project root:
--
--   sudo mysql icaro_ops < db/mysql/999_apply_algeria_patch.sql

SOURCE db/mysql/010_alter_airports_for_source_fields.sql;
SOURCE db/mysql/011_seed_icao_prefixes_algeria.sql;
SOURCE db/mysql/012_seed_airports_algeria.sql;
SOURCE db/mysql/013_verify_algeria_airports.sql;
