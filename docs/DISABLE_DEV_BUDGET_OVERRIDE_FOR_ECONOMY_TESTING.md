# Disable developer budget override for economy testing

This migration disables the local developer budget override used for unrestricted testing.

The override forced Luca's company budget to `999999999999.00` through a MySQL trigger, so economy changes were hidden after purchases, revenue, costs, penalties or other company updates.

## Apply

```bash
sudo mysql icaro_ops < db/mysql/118_disable_dev_budget_override_for_economy_testing.sql
```

## Verify

```bash
sudo mysql icaro_ops -e "
SELECT
  c.id,
  c.company_name,
  c.budget_amount,
  d.enabled AS dev_budget_override_enabled
FROM companies c
LEFT JOIN dev_budget_overrides d
  ON d.company_id = c.id
ORDER BY c.id;
"
```

Expected: `dev_budget_override_enabled = 0` for Luca's developer company.

## Optional: set a realistic test budget

After disabling the override, set a budget suitable for economy tests:

```bash
sudo mysql icaro_ops -e "
UPDATE companies
SET budget_amount = 25000000.00
WHERE id = 2;
"
```

Adapt the company id and amount to the local test scenario.
