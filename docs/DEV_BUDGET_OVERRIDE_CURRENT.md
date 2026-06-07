# Developer current budget override

## Reason

The previous patch introduced a `max_budget_amount`, but that concept is misleading.

For local development, we do not need a gameplay maximum. We need a developer override that forces the current budget of the development company to a very high value.

## Apply

```bash
cd /home/luca/Documenti/html/icaro-ops
unzip -o /home/luca/Scaricati/icaro-ops-dev-budget-override-current-patch.zip

sudo mysql icaro_ops < db/mysql/105_dev_budget_override_current.sql
```

## What changes

Creates:

```text
dev_budget_overrides
```

with:

```text
company_id
email
dev_budget_amount
enabled
reason
```

For:

```text
lucamezzolla@gmail.com
```

the development budget is set to:

```text
999999999999.00
```

## Important

This is not a maximum budget.

It is a current-budget override:

```text
current company budget = dev_budget_amount
```

The trigger:

```text
trg_companies_dev_budget_override_bu
```

keeps the company budget fixed at the developer override whenever `companies` is updated.

## Verify

```bash
sudo mysql icaro_ops -e "
SELECT
  c.id,
  c.company_name,
  c.budget_amount AS current_budget_amount,
  d.email,
  d.dev_budget_amount,
  d.enabled
FROM companies c
LEFT JOIN dev_budget_overrides d
  ON d.company_id = c.id
ORDER BY c.id;
"
```

You should see:

```text
999999999999.00
```

for the developer company.

## If you want to disable it later

```bash
sudo mysql icaro_ops -e "
UPDATE dev_budget_overrides
SET enabled = 0
WHERE email = 'lucamezzolla@gmail.com';
"
```
