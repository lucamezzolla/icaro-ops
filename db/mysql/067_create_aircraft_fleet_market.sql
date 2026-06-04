-- Icaro Ops aircraft catalog, company fleet and used-aircraft market.
--
-- Purpose:
--   Create the first aircraft model catalog with fully populated gameplay fields,
--   plus owned/leased aircraft instances and purchase offers between companies.
--
-- Notes:
--   - Values are initial gameplay/balancing values based on public aircraft specs.
--   - Prices and operating costs are estimates and should be reviewed periodically.
--   - Concorde is seeded as inactive/endgame so it exists in the catalog model,
--     but is not available in the early game.
--
-- Run:
--   sudo mysql icaro_ops < db/mysql/067_create_aircraft_fleet_market.sql

USE icaro_ops;

START TRANSACTION;

CREATE TABLE IF NOT EXISTS aircraft_models (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,

  manufacturer VARCHAR(80) NOT NULL,
  model_name VARCHAR(120) NOT NULL,
  model_code VARCHAR(40) NOT NULL,
  icao_type_code VARCHAR(8) NOT NULL,
  iata_type_code VARCHAR(8) NOT NULL,
  aircraft_family VARCHAR(80) NOT NULL,

  aircraft_category VARCHAR(40) NOT NULL,
  operation_role VARCHAR(40) NOT NULL,
  engine_type VARCHAR(40) NOT NULL,
  engine_count TINYINT UNSIGNED NOT NULL,

  crew_required_min TINYINT UNSIGNED NOT NULL,
  passenger_capacity_standard SMALLINT UNSIGNED NOT NULL,
  passenger_capacity_max SMALLINT UNSIGNED NOT NULL,
  cargo_capacity_kg INT UNSIGNED NOT NULL,
  max_payload_kg INT UNSIGNED NOT NULL,
  max_takeoff_weight_kg INT UNSIGNED NOT NULL,

  cruise_speed_kmh INT UNSIGNED NOT NULL,
  range_km INT UNSIGNED NOT NULL,
  service_ceiling_ft INT UNSIGNED NOT NULL,
  required_runway_m INT UNSIGNED NOT NULL,

  fuel_burn_kg_per_hour INT UNSIGNED NOT NULL,
  maintenance_cost_per_hour DECIMAL(12,2) NOT NULL,

  new_purchase_price DECIMAL(15,2) NOT NULL,
  estimated_used_price_min DECIMAL(15,2) NOT NULL,
  estimated_used_price_max DECIMAL(15,2) NOT NULL,
  lease_price_per_day DECIMAL(12,2) NOT NULL,
  currency_code CHAR(3) NOT NULL DEFAULT 'EUR',

  production_status VARCHAR(30) NOT NULL,
  is_available_new BOOLEAN NOT NULL DEFAULT TRUE,
  is_available_used BOOLEAN NOT NULL DEFAULT TRUE,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  is_endgame BOOLEAN NOT NULL DEFAULT FALSE,

  unlock_reputation_score INT NOT NULL DEFAULT 0,
  minimum_airport_size_tier VARCHAR(30) NOT NULL DEFAULT 'SMALL',

  gameplay_notes VARCHAR(500) NOT NULL,
  data_source_name VARCHAR(255) NOT NULL,
  data_source_url VARCHAR(500) NOT NULL,
  data_quality VARCHAR(30) NOT NULL DEFAULT 'PARTIAL',

  created_at_utc TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at_utc TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

  PRIMARY KEY (id),
  UNIQUE KEY uk_aircraft_models_model_code (model_code),
  KEY idx_aircraft_models_icao_type_code (icao_type_code),
  KEY idx_aircraft_models_category (aircraft_category),
  KEY idx_aircraft_models_operation_role (operation_role),
  KEY idx_aircraft_models_active_available (is_active, is_available_new, is_available_used),

  CONSTRAINT chk_aircraft_models_currency
    CHECK (currency_code IN ('EUR', 'USD')),

  CONSTRAINT chk_aircraft_models_engine_count
    CHECK (engine_count >= 1),

  CONSTRAINT chk_aircraft_models_passenger_capacity
    CHECK (passenger_capacity_max >= passenger_capacity_standard),

  CONSTRAINT chk_aircraft_models_prices
    CHECK (
      new_purchase_price >= 0
      AND estimated_used_price_min >= 0
      AND estimated_used_price_max >= estimated_used_price_min
      AND lease_price_per_day >= 0
    ),

  CONSTRAINT chk_aircraft_models_unlock
    CHECK (unlock_reputation_score BETWEEN 0 AND 100)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS company_aircraft (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,

  company_id BIGINT UNSIGNED NOT NULL,
  aircraft_model_id BIGINT UNSIGNED NOT NULL,

  registration_code VARCHAR(16) NOT NULL,
  serial_number VARCHAR(64) NOT NULL,
  manufacture_year SMALLINT UNSIGNED NOT NULL,

  ownership_status VARCHAR(30) NOT NULL DEFAULT 'OWNED',
  acquisition_type VARCHAR(30) NOT NULL DEFAULT 'NEW_PURCHASE',

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
  UNIQUE KEY uk_company_aircraft_registration_code (registration_code),
  KEY idx_company_aircraft_company (company_id),
  KEY idx_company_aircraft_model (aircraft_model_id),
  KEY idx_company_aircraft_status (status),
  KEY idx_company_aircraft_sale (is_available_for_sale, current_market_value),

  CONSTRAINT fk_company_aircraft_company
    FOREIGN KEY (company_id)
    REFERENCES companies(id)
    ON UPDATE CASCADE
    ON DELETE CASCADE,

  CONSTRAINT fk_company_aircraft_model
    FOREIGN KEY (aircraft_model_id)
    REFERENCES aircraft_models(id)
    ON UPDATE CASCADE
    ON DELETE RESTRICT,

  CONSTRAINT fk_company_aircraft_home_base
    FOREIGN KEY (home_base_icao_code)
    REFERENCES airports(icao_code)
    ON UPDATE CASCADE
    ON DELETE RESTRICT,

  CONSTRAINT fk_company_aircraft_current_airport
    FOREIGN KEY (current_airport_icao_code)
    REFERENCES airports(icao_code)
    ON UPDATE CASCADE
    ON DELETE RESTRICT,

  CONSTRAINT chk_company_aircraft_currency
    CHECK (currency_code IN ('EUR', 'USD')),

  CONSTRAINT chk_company_aircraft_condition
    CHECK (condition_percent BETWEEN 0 AND 100),

  CONSTRAINT chk_company_aircraft_hours_cycles
    CHECK (airframe_hours >= 0 AND cycles_count >= 0),

  CONSTRAINT chk_company_aircraft_prices
    CHECK (
      purchase_price >= 0
      AND current_market_value >= 0
      AND (asking_price IS NULL OR asking_price >= 0)
    ),

  CONSTRAINT chk_company_aircraft_ownership_status
    CHECK (ownership_status IN ('OWNED', 'LEASED')),

  CONSTRAINT chk_company_aircraft_acquisition_type
    CHECK (acquisition_type IN ('NEW_PURCHASE', 'USED_PURCHASE', 'LEASE', 'STARTER_CONTRACT', 'GAME_GRANT')),

  CONSTRAINT chk_company_aircraft_status
    CHECK (status IN ('PARKED', 'AVAILABLE', 'IN_FLIGHT', 'MAINTENANCE', 'LEASED_OUT', 'FOR_SALE', 'RETIRED'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS aircraft_purchase_offers (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,

  aircraft_id BIGINT UNSIGNED NOT NULL,
  buyer_company_id BIGINT UNSIGNED NOT NULL,
  seller_company_id BIGINT UNSIGNED NOT NULL,

  offered_amount DECIMAL(15,2) NOT NULL,
  currency_code CHAR(3) NOT NULL DEFAULT 'EUR',

  status VARCHAR(30) NOT NULL DEFAULT 'PENDING',
  seller_decision_reason VARCHAR(500) NULL,

  created_at_utc TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  expires_at_utc TIMESTAMP NOT NULL,
  decided_at_utc TIMESTAMP NULL,

  PRIMARY KEY (id),
  KEY idx_aircraft_purchase_offers_aircraft (aircraft_id),
  KEY idx_aircraft_purchase_offers_buyer (buyer_company_id),
  KEY idx_aircraft_purchase_offers_seller (seller_company_id),
  KEY idx_aircraft_purchase_offers_status (status, expires_at_utc),

  CONSTRAINT fk_aircraft_purchase_offers_aircraft
    FOREIGN KEY (aircraft_id)
    REFERENCES company_aircraft(id)
    ON UPDATE CASCADE
    ON DELETE CASCADE,

  CONSTRAINT fk_aircraft_purchase_offers_buyer
    FOREIGN KEY (buyer_company_id)
    REFERENCES companies(id)
    ON UPDATE CASCADE
    ON DELETE CASCADE,

  CONSTRAINT fk_aircraft_purchase_offers_seller
    FOREIGN KEY (seller_company_id)
    REFERENCES companies(id)
    ON UPDATE CASCADE
    ON DELETE CASCADE,

  CONSTRAINT chk_aircraft_purchase_offers_currency
    CHECK (currency_code IN ('EUR', 'USD')),

  CONSTRAINT chk_aircraft_purchase_offers_amount
    CHECK (offered_amount > 0),

  CONSTRAINT chk_aircraft_purchase_offers_status
    CHECK (status IN ('PENDING', 'ACCEPTED', 'REJECTED', 'EXPIRED', 'CANCELLED', 'COUNTER_OFFERED'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE OR REPLACE VIEW v_aircraft_market_listings AS
SELECT
  ca.id AS company_aircraft_id,
  ca.company_id AS seller_company_id,
  co.company_name AS seller_company_name,

  am.manufacturer,
  am.model_name,
  am.model_code,
  am.icao_type_code,
  am.aircraft_category,
  am.operation_role,

  ca.registration_code,
  ca.manufacture_year,
  ca.condition_percent,
  ca.airframe_hours,
  ca.cycles_count,
  ca.current_market_value,
  ca.asking_price,
  ca.currency_code,
  ca.current_airport_icao_code,
  ca.status,

  am.passenger_capacity_standard,
  am.cargo_capacity_kg,
  am.range_km,
  am.required_runway_m
FROM company_aircraft ca
JOIN companies co
  ON co.id = ca.company_id
JOIN aircraft_models am
  ON am.id = ca.aircraft_model_id
WHERE ca.is_available_for_sale = TRUE
  AND ca.status IN ('AVAILABLE', 'PARKED', 'FOR_SALE')
  AND ca.ownership_status = 'OWNED';

INSERT INTO aircraft_models (
  manufacturer,
  model_name,
  model_code,
  icao_type_code,
  iata_type_code,
  aircraft_family,
  aircraft_category,
  operation_role,
  engine_type,
  engine_count,
  crew_required_min,
  passenger_capacity_standard,
  passenger_capacity_max,
  cargo_capacity_kg,
  max_payload_kg,
  max_takeoff_weight_kg,
  cruise_speed_kmh,
  range_km,
  service_ceiling_ft,
  required_runway_m,
  fuel_burn_kg_per_hour,
  maintenance_cost_per_hour,
  new_purchase_price,
  estimated_used_price_min,
  estimated_used_price_max,
  lease_price_per_day,
  currency_code,
  production_status,
  is_available_new,
  is_available_used,
  is_active,
  is_endgame,
  unlock_reputation_score,
  minimum_airport_size_tier,
  gameplay_notes,
  data_source_name,
  data_source_url,
  data_quality
) VALUES
(
  'Textron Aviation / Cessna',
  '208B Grand Caravan EX',
  'C208B_GRAND_CARAVAN_EX',
  'C208',
  'CN1',
  'Cessna Caravan',
  'TURBOPROP_LIGHT',
  'PASSENGER_CARGO',
  'TURBOPROP',
  1,
  1,
  9,
  14,
  1300,
  1588,
  3996,
  340,
  1500,
  25000,
  430,
  170,
  420.00,
  3200000.00,
  1500000.00,
  2800000.00,
  4200.00,
  'EUR',
  'IN_PRODUCTION',
  TRUE,
  TRUE,
  TRUE,
  FALSE,
  0,
  'AIRSTRIP',
  'Early-game workhorse for small airports, short routes, passenger/cargo mixed operations and remote-field services.',
  'Textron/Cessna and public aircraft specification references',
  'https://cessna.txtav.com/en/turboprop/grand-caravan-ex',
  'PARTIAL'
),
(
  'Pilatus Aircraft',
  'PC-12 NGX',
  'PC12_NGX',
  'PC12',
  'PL2',
  'Pilatus PC-12',
  'TURBOPROP_LIGHT',
  'PASSENGER_CARGO',
  'TURBOPROP',
  1,
  1,
  8,
  10,
  1000,
  1200,
  4740,
  537,
  2898,
  30000,
  800,
  230,
  620.00,
  6000000.00,
  3500000.00,
  5600000.00,
  7600.00,
  'EUR',
  'IN_PRODUCTION',
  TRUE,
  TRUE,
  TRUE,
  FALSE,
  8,
  'SMALL',
  'Premium single-engine turboprop for executive, charter and mixed passenger/cargo regional routes.',
  'Pilatus technical data and public aircraft market references',
  'https://www.pilatus-aircraft.com/en/pc-12/technical-data',
  'PARTIAL'
),
(
  'Textron Aviation / Beechcraft',
  'King Air 360',
  'B350_KING_AIR_360',
  'B350',
  'BE3',
  'Beechcraft King Air',
  'TURBOPROP_LIGHT',
  'CHARTER',
  'TURBOPROP',
  2,
  1,
  8,
  11,
  520,
  1450,
  6804,
  578,
  3345,
  35000,
  1000,
  300,
  780.00,
  7800000.00,
  4200000.00,
  7200000.00,
  9800.00,
  'EUR',
  'IN_PRODUCTION',
  TRUE,
  TRUE,
  TRUE,
  FALSE,
  12,
  'SMALL',
  'Fast premium turboprop for business, VIP, charter and high-yield regional services.',
  'Beechcraft/Textron technical data and public aircraft specification references',
  'https://beechcraft.txtav.com/en/king-air-360',
  'PARTIAL'
),
(
  'De Havilland Canada',
  'DHC-6 Twin Otter Series 400',
  'DHC6_TWIN_OTTER_400',
  'DHC6',
  'DHT',
  'DHC-6 Twin Otter',
  'TURBOPROP_STOL',
  'PASSENGER_CARGO',
  'TURBOPROP',
  2,
  2,
  19,
  19,
  1800,
  2111,
  5670,
  337,
  1480,
  25000,
  370,
  260,
  520.00,
  6200000.00,
  2500000.00,
  5200000.00,
  7600.00,
  'EUR',
  'IN_PRODUCTION',
  TRUE,
  TRUE,
  TRUE,
  FALSE,
  10,
  'AIRSTRIP',
  'STOL aircraft for remote airports, island hopping, rough strips and mixed passenger/cargo services.',
  'De Havilland Canada technical data and public specification references',
  'https://dehavilland.com/twin-otter/',
  'PARTIAL'
),
(
  'Aircraft Industries',
  'L 410 NG',
  'L410_NG',
  'L410',
  'L4T',
  'Let L-410',
  'TURBOPROP_COMMUTER',
  'PASSENGER_CARGO',
  'TURBOPROP',
  2,
  2,
  19,
  19,
  1800,
  2150,
  7000,
  417,
  2100,
  13000,
  590,
  300,
  500.00,
  5800000.00,
  1800000.00,
  5000000.00,
  6900.00,
  'EUR',
  'IN_PRODUCTION',
  TRUE,
  TRUE,
  TRUE,
  FALSE,
  10,
  'SMALL',
  'Short-field 19-seat commuter aircraft for early regional airline growth and cargo-compatible routes.',
  'Aircraft Industries official specification and public aircraft references',
  'https://www.let.cz/en/l410ng',
  'PARTIAL'
),
(
  'Saab',
  '340B',
  'SAAB_340B',
  'SF34',
  'SF3',
  'Saab 340',
  'TURBOPROP_REGIONAL',
  'PASSENGER',
  'TURBOPROP',
  2,
  2,
  34,
  34,
  1200,
  3400,
  13154,
  524,
  1350,
  25000,
  1285,
  720,
  1050.00,
  0.00,
  800000.00,
  2600000.00,
  4200.00,
  'EUR',
  'OUT_OF_PRODUCTION',
  FALSE,
  TRUE,
  TRUE,
  FALSE,
  18,
  'MEDIUM',
  'Used-market regional turboprop for passenger routes after the first expansion phase.',
  'Saab official specification and public aircraft references',
  'https://www.saab.com/products/saab-340',
  'PARTIAL'
),
(
  'ATR',
  'ATR 42-600',
  'ATR42_600',
  'AT45',
  'AT4',
  'ATR 42',
  'TURBOPROP_REGIONAL',
  'PASSENGER',
  'TURBOPROP',
  2,
  2,
  48,
  48,
  700,
  5250,
  18600,
  556,
  1302,
  25000,
  1165,
  760,
  1350.00,
  21000000.00,
  8500000.00,
  18000000.00,
  18500.00,
  'EUR',
  'IN_PRODUCTION',
  TRUE,
  TRUE,
  TRUE,
  FALSE,
  28,
  'REGIONAL',
  'First larger regional airliner, suitable for stronger demand routes and medium regional airports.',
  'ATR official aircraft data and factsheet references',
  'https://www.atr-aircraft.com/aircraft-services/aircraft-family/atr-42-600/',
  'PARTIAL'
),
(
  'Embraer',
  'EMB 120ER Brasilia',
  'EMB120ER_BRASILIA',
  'E120',
  'EM2',
  'Embraer EMB 120',
  'TURBOPROP_REGIONAL',
  'PASSENGER_CARGO',
  'TURBOPROP',
  2,
  2,
  30,
  30,
  1200,
  3272,
  11990,
  500,
  2740,
  32000,
  1560,
  650,
  950.00,
  0.00,
  700000.00,
  2200000.00,
  3500.00,
  'EUR',
  'OUT_OF_PRODUCTION',
  FALSE,
  TRUE,
  TRUE,
  FALSE,
  16,
  'MEDIUM',
  'Used-market commuter aircraft for passenger routes and quick-change cargo opportunities.',
  'Public EMB 120 specification references',
  'https://www.globalair.com/aircraft-specifications/embraer/embraer-120er-specifications/830',
  'PARTIAL'
),
(
  'Aérospatiale/BAC',
  'Concorde',
  'CONCORDE',
  'CONC',
  'SSC',
  'Concorde',
  'SUPERSONIC',
  'PASSENGER',
  'TURBOJET',
  4,
  3,
  100,
  128,
  0,
  12700,
  185070,
  2179,
  7250,
  60000,
  3600,
  20000,
  90000.00,
  0.00,
  150000000.00,
  350000000.00,
  0.00,
  'EUR',
  'RETIRED',
  FALSE,
  FALSE,
  FALSE,
  TRUE,
  95,
  'HUB',
  'Endgame/special aircraft placeholder. Not available in early gameplay; requires future special rules, certification, maintenance and suitable airports.',
  'Public Concorde aircraft references',
  'https://en.wikipedia.org/wiki/Concorde',
  'PARTIAL'
)
ON DUPLICATE KEY UPDATE
  manufacturer = VALUES(manufacturer),
  model_name = VALUES(model_name),
  icao_type_code = VALUES(icao_type_code),
  iata_type_code = VALUES(iata_type_code),
  aircraft_family = VALUES(aircraft_family),
  aircraft_category = VALUES(aircraft_category),
  operation_role = VALUES(operation_role),
  engine_type = VALUES(engine_type),
  engine_count = VALUES(engine_count),
  crew_required_min = VALUES(crew_required_min),
  passenger_capacity_standard = VALUES(passenger_capacity_standard),
  passenger_capacity_max = VALUES(passenger_capacity_max),
  cargo_capacity_kg = VALUES(cargo_capacity_kg),
  max_payload_kg = VALUES(max_payload_kg),
  max_takeoff_weight_kg = VALUES(max_takeoff_weight_kg),
  cruise_speed_kmh = VALUES(cruise_speed_kmh),
  range_km = VALUES(range_km),
  service_ceiling_ft = VALUES(service_ceiling_ft),
  required_runway_m = VALUES(required_runway_m),
  fuel_burn_kg_per_hour = VALUES(fuel_burn_kg_per_hour),
  maintenance_cost_per_hour = VALUES(maintenance_cost_per_hour),
  new_purchase_price = VALUES(new_purchase_price),
  estimated_used_price_min = VALUES(estimated_used_price_min),
  estimated_used_price_max = VALUES(estimated_used_price_max),
  lease_price_per_day = VALUES(lease_price_per_day),
  currency_code = VALUES(currency_code),
  production_status = VALUES(production_status),
  is_available_new = VALUES(is_available_new),
  is_available_used = VALUES(is_available_used),
  is_active = VALUES(is_active),
  is_endgame = VALUES(is_endgame),
  unlock_reputation_score = VALUES(unlock_reputation_score),
  minimum_airport_size_tier = VALUES(minimum_airport_size_tier),
  gameplay_notes = VALUES(gameplay_notes),
  data_source_name = VALUES(data_source_name),
  data_source_url = VALUES(data_source_url),
  data_quality = VALUES(data_quality);

SELECT
  manufacturer,
  model_name,
  model_code,
  aircraft_category,
  operation_role,
  passenger_capacity_standard,
  cargo_capacity_kg,
  range_km,
  required_runway_m,
  new_purchase_price,
  is_active,
  is_endgame
FROM aircraft_models
ORDER BY is_endgame, unlock_reputation_score, manufacturer, model_name;

COMMIT;
