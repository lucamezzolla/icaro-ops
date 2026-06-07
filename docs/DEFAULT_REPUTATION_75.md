# Default company reputation 75

## Goal

A newly registered company should start with:

```text
reputation_score = 75 / 100
```

not with a very low reputation.

## Apply

```bash
cd /home/luca/Documenti/html/icaro-ops
unzip -o /home/luca/Scaricati/icaro-ops-default-reputation-75-patch.zip

sudo mysql icaro_ops < db/mysql/107_default_reputation_75.sql
```

## Verify

```bash
sudo mysql icaro_ops -e "
SELECT
  id,
  company_name,
  reputation_score
FROM companies
ORDER BY id;
"
```

Expected for the current development company:

```text
reputation_score = 75
```

## What it does

```text
- changes companies.reputation_score default to 75
- resets existing local companies to 75
- clamps reputation inside 0..100
```
