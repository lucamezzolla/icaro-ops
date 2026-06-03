-- ICAO prefixes.
-- ICAO remains a primary aviation concept in the DB.
-- Prefixes are linked to countries/territories but are not the first UI navigation level.

USE icaro_ops;

CREATE TABLE IF NOT EXISTS icao_prefixes (
  prefix VARCHAR(4) NOT NULL,
  country_id BIGINT UNSIGNED NOT NULL,

  area_name VARCHAR(180) NULL,
  notes VARCHAR(255) NULL,

  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at_utc TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at_utc TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

  PRIMARY KEY (prefix),
  KEY idx_icao_prefixes_country (country_id),

  CONSTRAINT fk_icao_prefixes_country
    FOREIGN KEY (country_id)
    REFERENCES countries(id)
    ON UPDATE CASCADE
    ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
