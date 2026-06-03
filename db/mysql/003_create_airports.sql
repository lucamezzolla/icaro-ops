-- Airports.
-- This table stores real-world descriptive airport data in English.
-- Game-specific values are intentionally kept in airport_game_profiles.

USE icaro_ops;

CREATE TABLE IF NOT EXISTS airports (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  icao_prefix_id BIGINT UNSIGNED NOT NULL,

  icao_code CHAR(4) NOT NULL,
  iata_code CHAR(3) NULL,

  name VARCHAR(180) NOT NULL,
  city VARCHAR(140) NOT NULL,
  country_name VARCHAR(140) NOT NULL,
  subdivision_name VARCHAR(140) NULL,

  latitude DECIMAL(10,7) NULL,
  longitude DECIMAL(10,7) NULL,
  elevation_ft INT NULL,

  is_civilian BOOLEAN NOT NULL DEFAULT TRUE,
  is_commercial BOOLEAN NOT NULL DEFAULT FALSE,
  is_military BOOLEAN NOT NULL DEFAULT FALSE,
  is_closed BOOLEAN NOT NULL DEFAULT FALSE,

  data_source_name VARCHAR(120) NULL,
  data_source_url VARCHAR(500) NULL,
  data_quality ENUM('UNVERIFIED', 'PARTIAL', 'VERIFIED') NOT NULL DEFAULT 'UNVERIFIED',
  verified_at_utc DATETIME NULL,

  created_at_utc TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at_utc TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

  PRIMARY KEY (id),
  UNIQUE KEY uk_airports_icao_code (icao_code),
  KEY idx_airports_prefix (icao_prefix_id),
  KEY idx_airports_country_city (country_name, city),
  KEY idx_airports_commercial_closed (is_commercial, is_closed),
  KEY idx_airports_location (latitude, longitude),

  CONSTRAINT fk_airports_icao_prefix
    FOREIGN KEY (icao_prefix_id)
    REFERENCES icao_prefixes(id)
    ON UPDATE CASCADE
    ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
