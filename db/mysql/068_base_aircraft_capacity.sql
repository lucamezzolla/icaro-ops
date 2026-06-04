-- Icaro Ops base aircraft capacity.
--
-- Purpose:
--   Add per-base aircraft capacity for player bases and virtual rival bases.
--   This is different from airport base slots:
--
--     airport base slots = how many companies can have a base at the airport
--     aircraft capacity = how many aircraft each base can manage/park
--
-- Requires:
--   airport_capacity_profiles
--   aircraft_models
--   company_aircraft
--   rival_companies
--   rival_company_bases
--
-- Run:
--   sudo mysql icaro_ops < db/mysql/068_base_aircraft_capacity.sql

USE icaro_ops;

START TRANSACTION;

ALTER TABLE airport_capacity_profiles
  ADD COLUMN IF NOT EXISTS max_aircraft_per_player_base INT NOT NULL DEFAULT 4 AFTER max_total_bases,
  ADD COLUMN IF NOT EXISTS max_aircraft_per_rival_base INT NOT NULL DEFAULT 4 AFTER max_aircraft_per_player_base,
  ADD COLUMN IF NOT EXISTS max_aircraft_on_ground_per_base INT NOT NULL DEFAULT 2 AFTER max_aircraft_per_rival_base;

-- Apply global first-pass capacity rules to every airport profile.
UPDATE airport_capacity_profiles
SET
  max_aircraft_per_player_base =
    CASE airport_size_tier
      WHEN 'CLOSED' THEN 0
      WHEN 'RESTRICTED' THEN 0
      WHEN 'AIRSTRIP' THEN 2
      WHEN 'SMALL' THEN 4
      WHEN 'MEDIUM' THEN 6
      WHEN 'REGIONAL' THEN 12
      WHEN 'HUB' THEN 30
      ELSE 4
    END,
  max_aircraft_per_rival_base =
    CASE airport_size_tier
      WHEN 'CLOSED' THEN 0
      WHEN 'RESTRICTED' THEN 0
      WHEN 'AIRSTRIP' THEN 2
      WHEN 'SMALL' THEN 4
      WHEN 'MEDIUM' THEN 6
      WHEN 'REGIONAL' THEN 12
      WHEN 'HUB' THEN 30
      ELSE 4
    END,
  max_aircraft_on_ground_per_base =
    CASE airport_size_tier
      WHEN 'CLOSED' THEN 0
      WHEN 'RESTRICTED' THEN 0
      WHEN 'AIRSTRIP' THEN 1
      WHEN 'SMALL' THEN 2
      WHEN 'MEDIUM' THEN 4
      WHEN 'REGIONAL' THEN 8
      WHEN 'HUB' THEN 20
      ELSE 2
    END;

-- Manual reviewed override: LIRA / Rome Ciampino.
UPDATE airport_capacity_profiles
SET
  airport_size_tier = 'MEDIUM',
  max_player_bases = 1,
  max_rival_bases = 1,
  max_total_bases = 2,
  max_aircraft_per_player_base = 6,
  max_aircraft_per_rival_base = 6,
  max_aircraft_on_ground_per_base = 4,
  note = 'Rome Ciampino: medium starting airport, max 2 total bases; each base manages up to 6 aircraft, with 4 on ground.'
WHERE airport_icao_code = 'LIRA';

CREATE TABLE IF NOT EXISTS rival_company_aircraft (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,

  rival_company_id BIGINT UNSIGNED NOT NULL,
  aircraft_model_id BIGINT UNSIGNED NOT NULL,

  registration_code VARCHAR(16) NOT NULL,
  serial_number VARCHAR(64) NOT NULL,
  manufacture_year SMALLINT UNSIGNED NOT NULL,

  ownership_status VARCHAR(30) NOT NULL DEFAULT 'OWNED',
  acquisition_type VARCHAR(30) NOT NULL DEFAULT 'USED_PURCHASE',

  purchase_price DECIMAL(15,2) NOT NULL DEFAULT 0.00,
  current_market_value DECIMAL(15,2) NOT NULL DEFAULT 0.00,
  currency_code CHAR(3) NOT NULL DEFAULT 'EUR',

  home_base_icao_code CHAR(4) NOT NULL,
  current_airport_icao_code CHAR(4) NOT NULL,

  condition_percent DECIMAL(5,2) NOT NULL DEFAULT 100.00,
  airframe_hours DECIMAL(12,2) NOT NULL DEFAULT 0.00,
  cycles_count INT UNSIGNED NOT NULL DEFAULT 0,

  status VARCHAR(30) NOT NULL DEFAULT 'PARKED',
  is_available_for_sale BOOLEAN NOT NULL DEFAULT FALSE,
  asking_price DECIMAL(15,2) NULL,

  created_at_utc TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at_utc TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

  PRIMARY KEY (id),
  UNIQUE KEY uk_rival_company_aircraft_registration_code (registration_code),
  KEY idx_rival_company_aircraft_company (rival_company_id),
  KEY idx_rival_company_aircraft_model (aircraft_model_id),
  KEY idx_rival_company_aircraft_status (status),
  KEY idx_rival_company_aircraft_sale (is_available_for_sale, current_market_value),

  CONSTRAINT fk_rival_company_aircraft_company
    FOREIGN KEY (rival_company_id)
    REFERENCES rival_companies(id)
    ON UPDATE CASCADE
    ON DELETE CASCADE,

  CONSTRAINT fk_rival_company_aircraft_model
    FOREIGN KEY (aircraft_model_id)
    REFERENCES aircraft_models(id)
    ON UPDATE CASCADE
    ON DELETE RESTRICT,

  CONSTRAINT fk_rival_company_aircraft_home_base
    FOREIGN KEY (home_base_icao_code)
    REFERENCES airports(icao_code)
    ON UPDATE CASCADE
    ON DELETE RESTRICT,

  CONSTRAINT fk_rival_company_aircraft_current_airport
    FOREIGN KEY (current_airport_icao_code)
    REFERENCES airports(icao_code)
    ON UPDATE CASCADE
    ON DELETE RESTRICT,

  CONSTRAINT chk_rival_company_aircraft_currency
    CHECK (currency_code IN ('EUR', 'USD')),

  CONSTRAINT chk_rival_company_aircraft_condition
    CHECK (condition_percent BETWEEN 0 AND 100),

  CONSTRAINT chk_rival_company_aircraft_hours_cycles
    CHECK (airframe_hours >= 0 AND cycles_count >= 0),

  CONSTRAINT chk_rival_company_aircraft_prices
    CHECK (
      purchase_price >= 0
      AND current_market_value >= 0
      AND (asking_price IS NULL OR asking_price >= 0)
    ),

  CONSTRAINT chk_rival_company_aircraft_ownership_status
    CHECK (ownership_status IN ('OWNED', 'LEASED')),

  CONSTRAINT chk_rival_company_aircraft_acquisition_type
    CHECK (acquisition_type IN ('NEW_PURCHASE', 'USED_PURCHASE', 'LEASE', 'STARTER_CONTRACT', 'GAME_GRANT')),

  CONSTRAINT chk_rival_company_aircraft_status
    CHECK (status IN ('PARKED', 'AVAILABLE', 'IN_FLIGHT', 'MAINTENANCE', 'LEASED_OUT', 'FOR_SALE', 'RETIRED'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Development seed: give the first virtual rival at LIRA one test aircraft,
-- so the dashboard can show rival fleet capacity immediately.
INSERT INTO rival_company_aircraft (
  rival_company_id,
  aircraft_model_id,
  registration_code,
  serial_number,
  manufacture_year,
  ownership_status,
  acquisition_type,
  purchase_price,
  current_market_value,
  currency_code,
  home_base_icao_code,
  current_airport_icao_code,
  condition_percent,
  airframe_hours,
  cycles_count,
  status,
  is_available_for_sale,
  asking_price
)
SELECT
  rc.id,
  am.id,
  'VR-LIRA-01',
  'SIM-AURELIA-LIRA-001',
  2014,
  'OWNED',
  'USED_PURCHASE',
  1450000.00,
  1280000.00,
  'EUR',
  'LIRA',
  'LIRA',
  82.50,
  6120.00,
  4820,
  'AVAILABLE',
  FALSE,
  NULL
FROM rival_companies rc
JOIN aircraft_models am
  ON am.model_code = 'C208B_GRAND_CARAVAN_EX'
JOIN airports a
  ON a.icao_code = 'LIRA'
WHERE rc.company_name = 'Aurelia Air Services'
ON DUPLICATE KEY UPDATE
  current_market_value = VALUES(current_market_value),
  condition_percent = VALUES(condition_percent),
  status = VALUES(status),
  is_available_for_sale = VALUES(is_available_for_sale);

CREATE OR REPLACE VIEW v_player_base_aircraft_capacity_status AS
SELECT
  co.id AS company_id,
  co.company_name,
  co.base_airport_icao_code AS airport_icao_code,

  acp.airport_size_tier,
  acp.max_aircraft_per_player_base AS max_aircraft_managed,
  acp.max_aircraft_on_ground_per_base AS max_aircraft_on_ground,

  COALESCE(COUNT(ca.id), 0) AS aircraft_owned_count,

  COALESCE(SUM(CASE
    WHEN ca.status IN ('PARKED', 'AVAILABLE', 'MAINTENANCE')
     AND ca.current_airport_icao_code = co.base_airport_icao_code
    THEN 1 ELSE 0
  END), 0) AS aircraft_at_base_count,

  COALESCE(SUM(CASE
    WHEN ca.status = 'IN_FLIGHT'
    THEN 1 ELSE 0
  END), 0) AS aircraft_in_flight_count,

  COALESCE(SUM(CASE
    WHEN ca.status = 'MAINTENANCE'
    THEN 1 ELSE 0
  END), 0) AS aircraft_maintenance_count,

  GREATEST(acp.max_aircraft_per_player_base - COALESCE(COUNT(ca.id), 0), 0) AS free_managed_aircraft_slots,

  GREATEST(
    acp.max_aircraft_on_ground_per_base -
    COALESCE(SUM(CASE
      WHEN ca.status IN ('PARKED', 'AVAILABLE', 'MAINTENANCE')
       AND ca.current_airport_icao_code = co.base_airport_icao_code
      THEN 1 ELSE 0
    END), 0),
    0
  ) AS free_ground_aircraft_slots

FROM companies co
JOIN airport_capacity_profiles acp
  ON acp.airport_icao_code = co.base_airport_icao_code
LEFT JOIN company_aircraft ca
  ON ca.company_id = co.id
 AND ca.home_base_icao_code = co.base_airport_icao_code
 AND ca.status <> 'RETIRED'
GROUP BY
  co.id,
  co.company_name,
  co.base_airport_icao_code,
  acp.airport_size_tier,
  acp.max_aircraft_per_player_base,
  acp.max_aircraft_on_ground_per_base;

CREATE OR REPLACE VIEW v_rival_base_aircraft_capacity_status AS
SELECT
  rc.id AS rival_company_id,
  rc.company_name,
  rb.airport_icao_code,

  acp.airport_size_tier,
  acp.max_aircraft_per_rival_base AS max_aircraft_managed,
  acp.max_aircraft_on_ground_per_base AS max_aircraft_on_ground,

  COALESCE(COUNT(ra.id), 0) AS aircraft_owned_count,

  COALESCE(SUM(CASE
    WHEN ra.status IN ('PARKED', 'AVAILABLE', 'MAINTENANCE')
     AND ra.current_airport_icao_code = rb.airport_icao_code
    THEN 1 ELSE 0
  END), 0) AS aircraft_at_base_count,

  COALESCE(SUM(CASE
    WHEN ra.status = 'IN_FLIGHT'
    THEN 1 ELSE 0
  END), 0) AS aircraft_in_flight_count,

  COALESCE(SUM(CASE
    WHEN ra.status = 'MAINTENANCE'
    THEN 1 ELSE 0
  END), 0) AS aircraft_maintenance_count,

  GREATEST(acp.max_aircraft_per_rival_base - COALESCE(COUNT(ra.id), 0), 0) AS free_managed_aircraft_slots,

  GREATEST(
    acp.max_aircraft_on_ground_per_base -
    COALESCE(SUM(CASE
      WHEN ra.status IN ('PARKED', 'AVAILABLE', 'MAINTENANCE')
       AND ra.current_airport_icao_code = rb.airport_icao_code
      THEN 1 ELSE 0
    END), 0),
    0
  ) AS free_ground_aircraft_slots

FROM rival_company_bases rb
JOIN rival_companies rc
  ON rc.id = rb.rival_company_id
JOIN airport_capacity_profiles acp
  ON acp.airport_icao_code = rb.airport_icao_code
LEFT JOIN rival_company_aircraft ra
  ON ra.rival_company_id = rc.id
 AND ra.home_base_icao_code = rb.airport_icao_code
 AND ra.status <> 'RETIRED'
WHERE rc.is_active = TRUE
GROUP BY
  rc.id,
  rc.company_name,
  rb.airport_icao_code,
  acp.airport_size_tier,
  acp.max_aircraft_per_rival_base,
  acp.max_aircraft_on_ground_per_base;

SELECT
  airport_icao_code,
  airport_size_tier,
  max_aircraft_managed,
  max_aircraft_on_ground,
  aircraft_owned_count,
  aircraft_at_base_count,
  aircraft_in_flight_count,
  aircraft_maintenance_count,
  free_managed_aircraft_slots,
  free_ground_aircraft_slots
FROM v_player_base_aircraft_capacity_status
WHERE airport_icao_code = 'LIRA';

SELECT
  airport_icao_code,
  company_name,
  airport_size_tier,
  max_aircraft_managed,
  max_aircraft_on_ground,
  aircraft_owned_count,
  aircraft_at_base_count,
  aircraft_in_flight_count,
  aircraft_maintenance_count,
  free_managed_aircraft_slots,
  free_ground_aircraft_slots
FROM v_rival_base_aircraft_capacity_status
WHERE airport_icao_code = 'LIRA';

COMMIT;
