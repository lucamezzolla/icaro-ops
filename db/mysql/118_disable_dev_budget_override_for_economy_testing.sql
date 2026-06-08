USE icaro_ops;

START TRANSACTION;

/*
 * Disable developer budget override for economy testing.
 *
 * The previous development override intentionally forced Luca's company budget
 * to 999999999999.00 on every companies update through a BEFORE UPDATE trigger.
 * That is useful for unrestricted aircraft/staff testing, but it hides real
 * economy changes because purchases, costs, revenue and penalties are always
 * overwritten by the fixed developer value.
 *
 * This migration keeps the dev_budget_overrides table for future use, but
 * disables the active override and drops the forcing trigger.
 */

DROP TRIGGER IF EXISTS trg_companies_dev_budget_override_bu;
DROP TRIGGER IF EXISTS trg_companies_dev_unlimited_budget_bu;

UPDATE dev_budget_overrides
SET enabled = 0,
    reason = 'Disabled for economy testing'
WHERE email = 'lucamezzolla@gmail.com';

COMMIT;

SELECT
  c.id,
  c.company_name,
  c.budget_amount AS current_budget_amount,
  d.email,
  d.dev_budget_amount,
  d.enabled AS dev_budget_override_enabled,
  d.reason
FROM companies c
LEFT JOIN dev_budget_overrides d
  ON d.company_id = c.id
ORDER BY c.id;
