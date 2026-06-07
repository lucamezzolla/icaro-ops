# Developer budget override single-company fallback fix

## Problem

The previous fallback assumed:

```text
company_id = 1
```

but the current local DB has:

```text
company_id = 2
company_name = Alitalia
```

So no override row was created.

## Apply

```bash
cd /home/luca/Documenti/html/icaro-ops
unzip -o /home/luca/Scaricati/icaro-ops-dev-budget-override-single-company-fix.zip

sudo mysql icaro_ops < db/mysql/106_dev_budget_override_single_company_fix.sql
```

## Verify

```bash
sudo mysql icaro_ops -e "
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
"
```

Expected for local development:

```text
Alitalia -> 999999999999.00
```

## Logic

If the user/company relation cannot be discovered from schema metadata:

```text
if there is exactly one company in the DB,
map the dev budget override to that company.
```

This is safer than assuming id 1.
