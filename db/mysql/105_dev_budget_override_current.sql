USE icaro_ops;

START TRANSACTION;

/*
 * Developer budget override.
 *
 * This is NOT a gameplay maximum budget.
 * It is a development/testing override that keeps the current company budget
 * at a fixed very high value for selected developer accounts/companies.
 */

DROP TRIGGER IF EXISTS trg_companies_dev_unlimited_budget_bu;
DROP TRIGGER IF EXISTS trg_companies_dev_budget_override_bu;

CREATE TABLE IF NOT EXISTS dev_budget_overrides (
  company_id BIGINT UNSIGNED NOT NULL PRIMARY KEY,
  email VARCHAR(190) NOT NULL,
  dev_budget_amount DECIMAL(14,2) NOT NULL DEFAULT 999999999999.00,
  enabled TINYINT(1) NOT NULL DEFAULT 1,
  reason VARCHAR(255) NOT NULL DEFAULT 'Developer testing budget override',
  created_at_utc TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at_utc TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_dev_budget_overrides_email (email),
  INDEX idx_dev_budget_overrides_enabled (enabled)
);

DROP PROCEDURE IF EXISTS refresh_dev_budget_overrides;

DELIMITER //

CREATE PROCEDURE refresh_dev_budget_overrides()
BEGIN
  DECLARE matched_count INT DEFAULT 0;

  /*
   * Clean previous Luca mapping and rebuild it from the current schema.
   */
  DELETE FROM dev_budget_overrides
  WHERE email = 'lucamezzolla@gmail.com';

  IF EXISTS (
    SELECT 1
    FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'users'
      AND COLUMN_NAME = 'email'
  ) THEN

    IF EXISTS (
      SELECT 1
      FROM information_schema.COLUMNS
      WHERE TABLE_SCHEMA = DATABASE()
        AND TABLE_NAME = 'companies'
        AND COLUMN_NAME = 'user_id'
    ) THEN
      INSERT IGNORE INTO dev_budget_overrides (
        company_id,
        email,
        dev_budget_amount,
        enabled,
        reason
      )
      SELECT
        c.id,
        'lucamezzolla@gmail.com',
        999999999999.00,
        1,
        'Developer account for local testing'
      FROM companies c
      JOIN users u
        ON u.id = c.user_id
      WHERE u.email = 'lucamezzolla@gmail.com';
    END IF;

    IF EXISTS (
      SELECT 1
      FROM information_schema.COLUMNS
      WHERE TABLE_SCHEMA = DATABASE()
        AND TABLE_NAME = 'companies'
        AND COLUMN_NAME = 'owner_user_id'
    ) THEN
      INSERT IGNORE INTO dev_budget_overrides (
        company_id,
        email,
        dev_budget_amount,
        enabled,
        reason
      )
      SELECT
        c.id,
        'lucamezzolla@gmail.com',
        999999999999.00,
        1,
        'Developer account for local testing'
      FROM companies c
      JOIN users u
        ON u.id = c.owner_user_id
      WHERE u.email = 'lucamezzolla@gmail.com';
    END IF;

    IF EXISTS (
      SELECT 1
      FROM information_schema.COLUMNS
      WHERE TABLE_SCHEMA = DATABASE()
        AND TABLE_NAME = 'companies'
        AND COLUMN_NAME = 'account_user_id'
    ) THEN
      INSERT IGNORE INTO dev_budget_overrides (
        company_id,
        email,
        dev_budget_amount,
        enabled,
        reason
      )
      SELECT
        c.id,
        'lucamezzolla@gmail.com',
        999999999999.00,
        1,
        'Developer account for local testing'
      FROM companies c
      JOIN users u
        ON u.id = c.account_user_id
      WHERE u.email = 'lucamezzolla@gmail.com';
    END IF;

    IF EXISTS (
      SELECT 1
      FROM information_schema.COLUMNS
      WHERE TABLE_SCHEMA = DATABASE()
        AND TABLE_NAME = 'companies'
        AND COLUMN_NAME = 'email'
    ) THEN
      INSERT IGNORE INTO dev_budget_overrides (
        company_id,
        email,
        dev_budget_amount,
        enabled,
        reason
      )
      SELECT
        c.id,
        'lucamezzolla@gmail.com',
        999999999999.00,
        1,
        'Developer account for local testing'
      FROM companies c
      WHERE c.email = 'lucamezzolla@gmail.com';
    END IF;
  END IF;

  SELECT COUNT(*)
  INTO matched_count
  FROM dev_budget_overrides
  WHERE email = 'lucamezzolla@gmail.com';

  /*
   * Local-development fallback.
   * If the user/company relation is not discoverable from schema metadata,
   * use company id 1, which is the local test company in the current dev DB.
   */
  IF matched_count = 0 THEN
    INSERT INTO dev_budget_overrides (
      company_id,
      email,
      dev_budget_amount,
      enabled,
      reason
    )
    SELECT
      c.id,
      'lucamezzolla@gmail.com',
      999999999999.00,
      1,
      'Developer account for local testing fallback'
    FROM companies c
    WHERE c.id = 1
    LIMIT 1
    ON DUPLICATE KEY UPDATE
      email = VALUES(email),
      dev_budget_amount = VALUES(dev_budget_amount),
      enabled = VALUES(enabled),
      reason = VALUES(reason);
  END IF;

  /*
   * This is the important part:
   * set the CURRENT budget now, not only a theoretical max/cap.
   */
  UPDATE companies c
  JOIN dev_budget_overrides d
    ON d.company_id = c.id
   AND d.enabled = 1
  SET c.budget_amount = d.dev_budget_amount;
END//

CREATE TRIGGER trg_companies_dev_budget_override_bu
BEFORE UPDATE ON companies
FOR EACH ROW
BEGIN
  DECLARE override_budget DECIMAL(14,2);

  SELECT d.dev_budget_amount
  INTO override_budget
  FROM dev_budget_overrides d
  WHERE d.company_id = NEW.id
    AND d.enabled = 1
  LIMIT 1;

  IF override_budget IS NOT NULL THEN
    SET NEW.budget_amount = override_budget;
  END IF;
END//

DELIMITER ;

CALL refresh_dev_budget_overrides();

/*
 * Optional cleanup of the older max-budget tables.
 * They are left in place if they exist, but no longer used by the new trigger.
 * Keeping them avoids accidental data loss while this patch is tested.
 */

COMMIT;

SELECT
  c.id,
  c.company_name,
  c.budget_amount AS current_budget_amount,
  d.email,
  d.dev_budget_amount,
  d.enabled,
  d.reason
FROM companies c
LEFT JOIN dev_budget_overrides d
  ON d.company_id = c.id
ORDER BY c.id;
