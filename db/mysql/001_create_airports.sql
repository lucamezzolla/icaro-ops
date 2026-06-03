-- Icaro Ops database schema draft.
-- Database content must stay in English. UI localization belongs to the frontend i18n layer.

CREATE TABLE airports (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  icao_code CHAR(4) NOT NULL,
  iata_code CHAR(3) NULL,
  name VARCHAR(160) NOT NULL,
  city VARCHAR(120) NOT NULL,
  country VARCHAR(120) NOT NULL,
  continent VARCHAR(60) NOT NULL,
  latitude DECIMAL(9,6) NOT NULL,
  longitude DECIMAL(9,6) NOT NULL,
  airport_size ENUM('SMALL_COMMERCIAL', 'MEDIUM_COMMERCIAL', 'LARGE_HUB') NOT NULL,
  is_starter_base BOOLEAN NOT NULL DEFAULT FALSE,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at_utc TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at_utc TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

  PRIMARY KEY (id),
  UNIQUE KEY uk_airports_icao_code (icao_code),
  KEY idx_airports_starter_base (is_starter_base, airport_size),
  KEY idx_airports_country_city (country, city)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
