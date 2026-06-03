-- Airlines.
-- Initial player company data.
-- Every new airline starts from current_balance = 0.

USE icaro_ops;

CREATE TABLE IF NOT EXISTS airlines (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,

  owner_user_id BIGINT UNSIGNED NULL,
  airline_name VARCHAR(120) NOT NULL,
  nickname VARCHAR(64) NOT NULL,

  account_currency CHAR(3) NOT NULL,
  current_balance DECIMAL(16,2) NOT NULL DEFAULT 0.00,

  base_airport_icao_code CHAR(4) NOT NULL,

  reputation_score DECIMAL(5,2) NOT NULL DEFAULT 0.00,
  safety_score DECIMAL(5,2) NOT NULL DEFAULT 0.00,
  punctuality_score DECIMAL(5,2) NOT NULL DEFAULT 0.00,

  last_simulated_at_utc DATETIME NOT NULL,
  created_at_utc TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at_utc TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

  PRIMARY KEY (id),
  KEY idx_airlines_base_airport (base_airport_icao_code),
  KEY idx_airlines_name (airline_name),

  CONSTRAINT chk_airlines_currency CHECK (account_currency IN ('EUR', 'USD')),
  CONSTRAINT chk_airlines_balance_zero_or_more CHECK (current_balance >= 0),
  CONSTRAINT fk_airlines_base_airport
    FOREIGN KEY (base_airport_icao_code)
    REFERENCES airports(icao_code)
    ON UPDATE CASCADE
    ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
