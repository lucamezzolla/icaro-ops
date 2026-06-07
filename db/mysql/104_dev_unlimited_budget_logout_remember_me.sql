USE icaro_ops;

START TRANSACTION;

CREATE TABLE IF NOT EXISTS dev_unlimited_budget_accounts (
  email VARCHAR(190) NOT NULL PRIMARY KEY,
  enabled TINYINT(1) NOT NULL DEFAULT 1,
  max_budget_amount DECIMAL(14,2) NOT NULL DEFAULT 999999999999.00,
  reason VARCHAR(255) NOT NULL DEFAULT 'Development and testing account',
  created_at_utc TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS dev_unlimited_budget_companies (
  company_id BIGINT UNSIGNED NOT NULL PRIMARY KEY,
  email VARCHAR(190) NOT NULL,
  max_budget_amount DECIMAL(14,2) NOT NULL DEFAULT 999999999999.00,
  created_at_utc TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_dev_unlimited_budget_companies_email (email)
);

INSERT INTO dev_unlimited_budget_accounts (email, enabled, max_budget_amount, reason)
VALUES ('lucamezzolla@gmail.com', 1, 999999999999.00, 'Developer account for local testing')
ON DUPLICATE KEY UPDATE
  enabled = VALUES(enabled),
  max_budget_amount = VALUES(max_budget_amount),
  reason = VALUES(reason);

DROP PROCEDURE IF EXISTS refresh_dev_unlimited_budget_companies;

DELIMITER //

CREATE PROCEDURE refresh_dev_unlimited_budget_companies()
BEGIN
  DECLARE matched_count INT DEFAULT 0;

  DELETE FROM dev_unlimited_budget_companies
  WHERE email IN (SELECT email FROM dev_unlimited_budget_accounts WHERE enabled = 1);

  IF EXISTS (SELECT 1 FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'users' AND COLUMN_NAME = 'email') THEN

    IF EXISTS (SELECT 1 FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'companies' AND COLUMN_NAME = 'user_id') THEN
      INSERT IGNORE INTO dev_unlimited_budget_companies (company_id, email, max_budget_amount)
      SELECT c.id, d.email, d.max_budget_amount
      FROM companies c
      JOIN users u ON u.id = c.user_id
      JOIN dev_unlimited_budget_accounts d ON d.email = u.email AND d.enabled = 1;
    END IF;

    IF EXISTS (SELECT 1 FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'companies' AND COLUMN_NAME = 'owner_user_id') THEN
      INSERT IGNORE INTO dev_unlimited_budget_companies (company_id, email, max_budget_amount)
      SELECT c.id, d.email, d.max_budget_amount
      FROM companies c
      JOIN users u ON u.id = c.owner_user_id
      JOIN dev_unlimited_budget_accounts d ON d.email = u.email AND d.enabled = 1;
    END IF;

    IF EXISTS (SELECT 1 FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'companies' AND COLUMN_NAME = 'account_user_id') THEN
      INSERT IGNORE INTO dev_unlimited_budget_companies (company_id, email, max_budget_amount)
      SELECT c.id, d.email, d.max_budget_amount
      FROM companies c
      JOIN users u ON u.id = c.account_user_id
      JOIN dev_unlimited_budget_accounts d ON d.email = u.email AND d.enabled = 1;
    END IF;

    IF EXISTS (SELECT 1 FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'companies' AND COLUMN_NAME = 'email') THEN
      INSERT IGNORE INTO dev_unlimited_budget_companies (company_id, email, max_budget_amount)
      SELECT c.id, d.email, d.max_budget_amount
      FROM companies c
      JOIN dev_unlimited_budget_accounts d ON d.email = c.email AND d.enabled = 1;
    END IF;
  END IF;

  SELECT COUNT(*) INTO matched_count FROM dev_unlimited_budget_companies;

  IF matched_count = 0 THEN
    INSERT IGNORE INTO dev_unlimited_budget_companies (company_id, email, max_budget_amount)
    SELECT c.id, 'lucamezzolla@gmail.com', 999999999999.00
    FROM companies c
    WHERE c.id = 1
    LIMIT 1;
  END IF;

  UPDATE companies c
  JOIN dev_unlimited_budget_companies d ON d.company_id = c.id
  SET c.budget_amount = d.max_budget_amount;
END//

DELIMITER ;

CALL refresh_dev_unlimited_budget_companies();

DROP TRIGGER IF EXISTS trg_companies_dev_unlimited_budget_bu;

DELIMITER //

CREATE TRIGGER trg_companies_dev_unlimited_budget_bu
BEFORE UPDATE ON companies
FOR EACH ROW
BEGIN
  DECLARE dev_max_budget DECIMAL(14,2);

  SELECT d.max_budget_amount
  INTO dev_max_budget
  FROM dev_unlimited_budget_companies d
  WHERE d.company_id = NEW.id
  LIMIT 1;

  IF dev_max_budget IS NOT NULL THEN
    IF NEW.budget_amount < dev_max_budget THEN
      SET NEW.budget_amount = dev_max_budget;
    END IF;
  END IF;
END//

DELIMITER ;

COMMIT;

SELECT c.id, c.company_name, c.budget_amount, d.email, d.max_budget_amount
FROM companies c
JOIN dev_unlimited_budget_companies d ON d.company_id = c.id;
