-- Icaro Ops authentication, initial budget and private session support.
--
-- Run:
--   sudo mysql icaro_ops < db/mysql/072_auth_initial_budget.sql

USE icaro_ops;

START TRANSACTION;

ALTER TABLE players
  ADD COLUMN IF NOT EXISTS email VARCHAR(190) NULL AFTER last_name,
  ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255) NULL AFTER email,
  ADD COLUMN IF NOT EXISTS last_login_at_utc TIMESTAMP NULL AFTER password_hash;

CREATE UNIQUE INDEX IF NOT EXISTS uk_players_email ON players(email);

-- New companies start with enough budget for early Fleet development tests.
-- Final gameplay can later replace this with tutorial financing, starter contract or leasing.
CREATE TABLE IF NOT EXISTS game_settings (
  setting_key VARCHAR(100) NOT NULL,
  setting_value VARCHAR(500) NOT NULL,
  updated_at_utc TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (setting_key)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO game_settings (setting_key, setting_value)
VALUES ('initial_company_budget', '7000000.00')
ON DUPLICATE KEY UPDATE setting_value = VALUES(setting_value);

SELECT setting_key, setting_value
FROM game_settings
WHERE setting_key = 'initial_company_budget';

COMMIT;
