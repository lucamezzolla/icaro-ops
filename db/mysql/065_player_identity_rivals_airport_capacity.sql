-- Icaro Ops player identity, rival companies and airport base capacity.
--
-- Requires:
--   062_create_starting_base_selection_view.sql
--   063_create_signup_company_tables.sql
--
-- Run:
--   sudo mysql icaro_ops < db/mysql/065_player_identity_rivals_airport_capacity.sql

USE icaro_ops;

START TRANSACTION;

ALTER TABLE players
  ADD COLUMN IF NOT EXISTS first_name VARCHAR(60) NULL AFTER id,
  ADD COLUMN IF NOT EXISTS last_name VARCHAR(60) NULL AFTER first_name;

-- Keep the old nickname column for backward compatibility during development.
-- New signups fill first_name/last_name and also write a generated nickname-like value.

CREATE TABLE IF NOT EXISTS airport_capacity_profiles (
  airport_icao_code CHAR(4) NOT NULL,

  airport_size_tier VARCHAR(30) NOT NULL DEFAULT 'UNCLASSIFIED',
  max_player_bases INT NOT NULL DEFAULT 1,
  max_rival_bases INT NOT NULL DEFAULT 0,
  max_total_bases INT NOT NULL DEFAULT 1,

  note VARCHAR(255) NULL,

  created_at_utc TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at_utc TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

  PRIMARY KEY (airport_icao_code),

  CONSTRAINT fk_airport_capacity_profiles_airport
    FOREIGN KEY (airport_icao_code)
    REFERENCES airports(icao_code)
    ON UPDATE CASCADE
    ON DELETE CASCADE,

  CONSTRAINT chk_airport_capacity_max_player
    CHECK (max_player_bases >= 0),

  CONSTRAINT chk_airport_capacity_max_rival
    CHECK (max_rival_bases >= 0),

  CONSTRAINT chk_airport_capacity_max_total
    CHECK (max_total_bases >= 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS rival_companies (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,

  company_name VARCHAR(80) NOT NULL,
  reputation_score INT NOT NULL DEFAULT 0,
  strategy_type VARCHAR(40) NOT NULL DEFAULT 'BALANCED',
  is_active BOOLEAN NOT NULL DEFAULT TRUE,

  created_at_utc TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at_utc TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

  PRIMARY KEY (id),
  UNIQUE KEY uk_rival_companies_company_name (company_name),

  CONSTRAINT chk_rival_companies_reputation_score
    CHECK (reputation_score BETWEEN 0 AND 100)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS rival_company_bases (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,

  rival_company_id BIGINT UNSIGNED NOT NULL,
  airport_icao_code CHAR(4) NOT NULL,
  base_role VARCHAR(30) NOT NULL DEFAULT 'PRIMARY',

  created_at_utc TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

  PRIMARY KEY (id),
  UNIQUE KEY uk_rival_company_bases_company_airport (rival_company_id, airport_icao_code),
  KEY idx_rival_company_bases_airport (airport_icao_code),

  CONSTRAINT fk_rival_company_bases_company
    FOREIGN KEY (rival_company_id)
    REFERENCES rival_companies(id)
    ON UPDATE CASCADE
    ON DELETE CASCADE,

  CONSTRAINT fk_rival_company_bases_airport
    FOREIGN KEY (airport_icao_code)
    REFERENCES airports(icao_code)
    ON UPDATE CASCADE
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Conservative automatic capacity seed for airports that can be used as starting bases.
-- This can be reviewed over time and overridden per airport.
INSERT INTO airport_capacity_profiles (
  airport_icao_code,
  airport_size_tier,
  max_player_bases,
  max_rival_bases,
  max_total_bases,
  note
)
SELECT
  v.icao_code,

  CASE
    WHEN v.service_category = 'INTERNATIONAL' THEN 'REGIONAL'
    WHEN v.airport_type = 'AIRFIELD' THEN 'SMALL'
    ELSE 'SMALL'
  END AS airport_size_tier,

  1 AS max_player_bases,

  CASE
    WHEN v.service_category = 'INTERNATIONAL' THEN 2
    ELSE 0
  END AS max_rival_bases,

  CASE
    WHEN v.service_category = 'INTERNATIONAL' THEN 3
    ELSE 1
  END AS max_total_bases,

  'Initial automatic capacity profile. Review periodically.'
FROM v_starting_base_airports v
ON DUPLICATE KEY UPDATE
  airport_size_tier = VALUES(airport_size_tier),
  max_player_bases = VALUES(max_player_bases),
  max_rival_bases = VALUES(max_rival_bases),
  max_total_bases = VALUES(max_total_bases),
  note = VALUES(note);

-- Ciampino is medium for gameplay: user + at most one virtual rival.
INSERT INTO airport_capacity_profiles (
  airport_icao_code,
  airport_size_tier,
  max_player_bases,
  max_rival_bases,
  max_total_bases,
  note
)
SELECT
  'LIRA',
  'MEDIUM',
  1,
  1,
  2,
  'Rome Ciampino: medium starting airport, max 2 total bases for early-game balancing.'
FROM airports
WHERE icao_code = 'LIRA'
ON DUPLICATE KEY UPDATE
  airport_size_tier = VALUES(airport_size_tier),
  max_player_bases = VALUES(max_player_bases),
  max_rival_bases = VALUES(max_rival_bases),
  max_total_bases = VALUES(max_total_bases),
  note = VALUES(note);

-- A tiny initial virtual rival set for development. These are not physical players.
INSERT INTO rival_companies (
  company_name,
  reputation_score,
  strategy_type
) VALUES
('Aurelia Air Services', 12, 'REGIONAL_PASSENGER'),
('Tyrrhenian Cargo Link', 9, 'LIGHT_CARGO')
ON DUPLICATE KEY UPDATE
  reputation_score = VALUES(reputation_score),
  strategy_type = VALUES(strategy_type),
  is_active = TRUE;

-- Put at most one rival at Ciampino as an example of local competition.
INSERT INTO rival_company_bases (
  rival_company_id,
  airport_icao_code,
  base_role
)
SELECT
  rc.id,
  'LIRA',
  'PRIMARY'
FROM rival_companies rc
JOIN airports a
  ON a.icao_code = 'LIRA'
WHERE rc.company_name = 'Aurelia Air Services'
ON DUPLICATE KEY UPDATE
  base_role = VALUES(base_role);

COMMIT;
