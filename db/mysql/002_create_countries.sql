-- Countries and territories used for base selection.
-- Names are stored in English. UI translations must be handled outside the DB.

USE icaro_ops;

CREATE TABLE IF NOT EXISTS countries (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  world_region_code VARCHAR(32) NOT NULL,

  name VARCHAR(160) NOT NULL,
  subregion_name VARCHAR(120) NULL,

  iso2_code CHAR(2) NULL,
  iso3_code CHAR(3) NULL,

  has_airports BOOLEAN NOT NULL DEFAULT TRUE,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,

  created_at_utc TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at_utc TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

  PRIMARY KEY (id),
  UNIQUE KEY uk_countries_region_name (world_region_code, name),
  KEY idx_countries_region_subregion (world_region_code, subregion_name),
  KEY idx_countries_name (name),

  CONSTRAINT fk_countries_world_region
    FOREIGN KEY (world_region_code)
    REFERENCES world_regions(code)
    ON UPDATE CASCADE
    ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
