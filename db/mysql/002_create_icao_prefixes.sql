-- ICAO prefixes.
-- A prefix can be one, two, three or four characters depending on the ICAO allocation level we store.
-- Examples:
--   LI   = Italy
--   LF   = France
--   EG   = United Kingdom
--   K    = Contiguous United States
--   C    = Canada
--   WIII = Jakarta / Soekarno-Hatta prefix-level special case when imported as a precise allocation

USE icaro_ops;

CREATE TABLE IF NOT EXISTS icao_prefixes (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  icao_region_id BIGINT UNSIGNED NOT NULL,
  prefix VARCHAR(4) NOT NULL,
  country_name VARCHAR(140) NOT NULL,
  area_name VARCHAR(180) NULL,
  notes VARCHAR(255) NULL,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at_utc TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at_utc TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

  PRIMARY KEY (id),
  UNIQUE KEY uk_icao_prefixes_prefix (prefix),
  KEY idx_icao_prefixes_region_country (icao_region_id, country_name),
  KEY idx_icao_prefixes_country_name (country_name),

  CONSTRAINT fk_icao_prefixes_region
    FOREIGN KEY (icao_region_id)
    REFERENCES icao_regions(id)
    ON UPDATE CASCADE
    ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
