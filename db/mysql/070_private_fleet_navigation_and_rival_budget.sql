-- Icaro Ops private navigation and rival budget.
--
-- Purpose:
--   Fleet should use the active company stored in the browser session,
--   not a visible companyId query parameter.
--
--   Also add budget data for virtual rivals so base details can show
--   approximate competitor financial strength.
--
-- Run:
--   sudo mysql icaro_ops < db/mysql/070_private_fleet_navigation_and_rival_budget.sql

USE icaro_ops;

START TRANSACTION;

ALTER TABLE rival_companies
  ADD COLUMN IF NOT EXISTS budget_amount DECIMAL(15,2) NOT NULL DEFAULT 0.00 AFTER reputation_score,
  ADD COLUMN IF NOT EXISTS currency_code CHAR(3) NOT NULL DEFAULT 'EUR' AFTER budget_amount;

UPDATE rival_companies
SET
  budget_amount = CASE
    WHEN company_name = 'Aurelia Air Services' THEN 250000.00
    WHEN company_name = 'Tyrrhenian Cargo Link' THEN 180000.00
    ELSE CASE
      WHEN budget_amount = 0.00 THEN 150000.00
      ELSE budget_amount
    END
  END,
  currency_code = CASE
    WHEN currency_code IS NULL OR currency_code = '' THEN 'EUR'
    ELSE currency_code
  END;

SELECT
  id,
  company_name,
  budget_amount,
  currency_code,
  reputation_score,
  strategy_type
FROM rival_companies
ORDER BY company_name;

COMMIT;
