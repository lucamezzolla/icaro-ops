-- Icaro Ops Antarctica airport patch.
-- Run from the project root:
--
--   sudo mysql icaro_ops < db/mysql/999_apply_antarctica_airports_patch.sql

SOURCE db/mysql/056_seed_airports_antarctica.sql;
