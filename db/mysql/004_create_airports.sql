-- Airports.
-- ICAO code is the primary key.
-- Airport list is intentionally empty in this DB version.
-- Future imports will populate this table from the long airport list.

USE icaro_ops;

CREATE TABLE IF NOT EXISTS airports (
  icao_code CHAR(4) NOT NULL,
  country_id BIGINT UNSIGNED NOT NULL,
  icao_prefix VARCHAR(4) NULL,

  iata_code CHAR(3) NULL,
  name VARCHAR(180) NOT NULL,
  city VARCHAR(140) NULL,
  location_name VARCHAR(180) NULL,
  subdivision_name VARCHAR(140) NULL,

  latitude DECIMAL(10,7) NULL,
  longitude DECIMAL(10,7) NULL,
  elevation_ft INT NULL,

  airport_type ENUM(
    'AIRPORT',
    'AIRFIELD',
    'AIRSTRIP',
    'HELIPORT',
    'SEAPLANE_BASE',
    'SKIWAY',
    'UNKNOWN'
  ) NOT NULL DEFAULT 'UNKNOWN',

  is_civilian BOOLEAN NOT NULL DEFAULT TRUE,
  is_commercial BOOLEAN NOT NULL DEFAULT FALSE,
  is_military BOOLEAN NOT NULL DEFAULT FALSE,
  is_closed BOOLEAN NOT NULL DEFAULT FALSE,

  operator_country_name VARCHAR(160) NULL,
  data_source_name VARCHAR(120) NULL,
  data_source_url VARCHAR(500) NULL,
  data_quality ENUM('UNVERIFIED', 'PARTIAL', 'VERIFIED') NOT NULL DEFAULT 'UNVERIFIED',
  verified_at_utc DATETIME NULL,

  created_at_utc TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at_utc TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

  PRIMARY KEY (icao_code),
  KEY idx_airports_country (country_id),
  KEY idx_airports_icao_prefix (icao_prefix),
  KEY idx_airports_country_city (country_id, city),
  KEY idx_airports_commercial_closed (is_commercial, is_closed),
  KEY idx_airports_location (latitude, longitude),

  CONSTRAINT fk_airports_country
    FOREIGN KEY (country_id)
    REFERENCES countries(id)
    ON UPDATE CASCADE
    ON DELETE RESTRICT,

  CONSTRAINT fk_airports_icao_prefix
    FOREIGN KEY (icao_prefix)
    REFERENCES icao_prefixes(prefix)
    ON UPDATE CASCADE
    ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
