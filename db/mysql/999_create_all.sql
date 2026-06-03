-- Icaro Ops complete local database bootstrap.
-- Run this file from the project root with:
--
--   mysql -u root -p < db/mysql/999_create_all.sql
--
-- Or run the individual files in numeric order.

SOURCE db/mysql/000_create_database.sql;
SOURCE db/mysql/001_create_world_regions.sql;
SOURCE db/mysql/002_create_countries.sql;
SOURCE db/mysql/003_create_icao_prefixes.sql;
SOURCE db/mysql/004_create_airports.sql;
SOURCE db/mysql/005_create_airport_game_profiles.sql;
SOURCE db/mysql/006_create_airlines.sql;
SOURCE db/mysql/007_seed_world_regions.sql;
SOURCE db/mysql/008_seed_countries.sql;
SOURCE db/mysql/009_views_base_selection.sql;
