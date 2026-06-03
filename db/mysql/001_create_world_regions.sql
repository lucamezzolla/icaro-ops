-- World regions used by the initial base selection flow.
-- User flow: world region -> country/territory -> airport.
-- Airports remain ICAO-primary.

USE icaro_ops;

CREATE TABLE IF NOT EXISTS world_regions (
  code VARCHAR(32) NOT NULL,
  name VARCHAR(80) NOT NULL,
  sort_order SMALLINT UNSIGNED NOT NULL DEFAULT 0,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at_utc TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at_utc TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

  PRIMARY KEY (code),
  UNIQUE KEY uk_world_regions_name (name),
  KEY idx_world_regions_sort_order (sort_order)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
