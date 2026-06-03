-- Airport game profiles.
-- Gameplay values are separated from real-world airport facts.
-- References airports by ICAO code.

USE icaro_ops;

CREATE TABLE IF NOT EXISTS airport_game_profiles (
  airport_icao_code CHAR(4) NOT NULL,

  airport_size ENUM(
    'TINY_AIRFIELD',
    'SMALL_COMMERCIAL',
    'MEDIUM_COMMERCIAL',
    'LARGE_HUB',
    'MEGA_HUB'
  ) NOT NULL,

  starter_base_allowed BOOLEAN NOT NULL DEFAULT FALSE,
  starter_difficulty ENUM('EASY', 'NORMAL', 'HARD') NULL,

  base_opening_cost DECIMAL(14,2) NOT NULL DEFAULT 0.00,
  monthly_base_cost DECIMAL(14,2) NOT NULL DEFAULT 0.00,

  slot_cost_level ENUM('LOW', 'MEDIUM', 'HIGH', 'EXTREME') NOT NULL DEFAULT 'LOW',

  passenger_demand_level ENUM(
    'VERY_LOW',
    'LOW',
    'MEDIUM',
    'HIGH',
    'VERY_HIGH'
  ) NOT NULL DEFAULT 'LOW',

  cargo_demand_level ENUM(
    'VERY_LOW',
    'LOW',
    'MEDIUM',
    'HIGH',
    'VERY_HIGH'
  ) NOT NULL DEFAULT 'LOW',

  max_aircraft_class ENUM(
    'HELICOPTER',
    'TURBOPROP',
    'REGIONAL_JET',
    'NARROW_BODY',
    'WIDE_BODY',
    'SUPERSONIC'
  ) NOT NULL DEFAULT 'TURBOPROP',

  created_at_utc TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at_utc TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

  PRIMARY KEY (airport_icao_code),
  KEY idx_airport_game_profiles_starter (starter_base_allowed, starter_difficulty),
  KEY idx_airport_game_profiles_size (airport_size),
  KEY idx_airport_game_profiles_max_aircraft (max_aircraft_class),

  CONSTRAINT fk_airport_game_profiles_airport
    FOREIGN KEY (airport_icao_code)
    REFERENCES airports(icao_code)
    ON UPDATE CASCADE
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
