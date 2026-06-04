-- Development-only reset.
--
-- Deletes player/session gameplay data while preserving master data:
-- countries, world_regions, airports, aircraft_models, capacity profiles.
--
-- Run:
--   sudo mysql icaro_ops < db/mysql/dev/901_reset_dev_players_companies.sql

USE icaro_ops;

SET FOREIGN_KEY_CHECKS = 0;

DELETE FROM aircraft_purchase_offers;
DELETE FROM company_aircraft;
DELETE FROM airport_base_slot_offers;
DELETE FROM company_market_offer_generation_state;
DELETE FROM companies;
DELETE FROM players;

ALTER TABLE aircraft_purchase_offers AUTO_INCREMENT = 1;
ALTER TABLE company_aircraft AUTO_INCREMENT = 1;
ALTER TABLE airport_base_slot_offers AUTO_INCREMENT = 1;
ALTER TABLE companies AUTO_INCREMENT = 1;
ALTER TABLE players AUTO_INCREMENT = 1;

SET FOREIGN_KEY_CHECKS = 1;

SELECT
  (SELECT COUNT(*) FROM players) AS players_count,
  (SELECT COUNT(*) FROM companies) AS companies_count,
  (SELECT COUNT(*) FROM company_aircraft) AS company_aircraft_count;
