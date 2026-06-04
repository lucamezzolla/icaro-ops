-- Icaro Ops signup/company bootstrap.
--
-- Requires:
--   db/mysql/062_create_starting_base_selection_view.sql
--
-- Run:
--   sudo mysql icaro_ops < db/mysql/063_create_signup_company_tables.sql

USE icaro_ops;

START TRANSACTION;

CREATE TABLE IF NOT EXISTS players (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  nickname VARCHAR(40) NOT NULL,
  interface_language VARCHAR(5) NOT NULL DEFAULT 'en',

  created_at_utc TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at_utc TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

  PRIMARY KEY (id),
  UNIQUE KEY uk_players_nickname (nickname)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS companies (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  player_id BIGINT UNSIGNED NOT NULL,

  company_name VARCHAR(80) NOT NULL,
  currency_code CHAR(3) NOT NULL,
  base_airport_icao_code CHAR(4) NOT NULL,

  budget_amount DECIMAL(15,2) NOT NULL DEFAULT 0.00,
  reputation_score INT NOT NULL DEFAULT 0,

  created_at_utc TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at_utc TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

  PRIMARY KEY (id),
  UNIQUE KEY uk_companies_player (player_id),
  UNIQUE KEY uk_companies_company_name (company_name),
  KEY idx_companies_base_airport (base_airport_icao_code),

  CONSTRAINT fk_companies_player
    FOREIGN KEY (player_id)
    REFERENCES players(id)
    ON UPDATE CASCADE
    ON DELETE CASCADE,

  CONSTRAINT fk_companies_base_airport
    FOREIGN KEY (base_airport_icao_code)
    REFERENCES airports(icao_code)
    ON UPDATE CASCADE
    ON DELETE RESTRICT,

  CONSTRAINT chk_companies_currency_code
    CHECK (currency_code IN ('EUR', 'USD')),

  CONSTRAINT chk_companies_budget_amount
    CHECK (budget_amount >= 0),

  CONSTRAINT chk_companies_reputation_score
    CHECK (reputation_score BETWEEN 0 AND 100)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS company_market_offer_generation_state (
  company_id BIGINT UNSIGNED NOT NULL,
  last_generated_at_utc TIMESTAMP NULL,
  next_generation_at_utc TIMESTAMP NULL,

  PRIMARY KEY (company_id),

  CONSTRAINT fk_company_market_offer_generation_state_company
    FOREIGN KEY (company_id)
    REFERENCES companies(id)
    ON UPDATE CASCADE
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

COMMIT;
