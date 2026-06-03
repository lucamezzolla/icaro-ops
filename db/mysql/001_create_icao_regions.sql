-- ICAO macro regions.
-- These are broad first-letter ICAO code groups used to guide airport selection.

USE icaro_ops;

CREATE TABLE IF NOT EXISTS icao_regions (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  region_code CHAR(1) NOT NULL,
  name VARCHAR(140) NOT NULL,
  description VARCHAR(255) NULL,
  sort_order SMALLINT UNSIGNED NOT NULL DEFAULT 0,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at_utc TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at_utc TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

  PRIMARY KEY (id),
  UNIQUE KEY uk_icao_regions_region_code (region_code),
  KEY idx_icao_regions_sort_order (sort_order)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
