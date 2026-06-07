# Fix model-detail strict_types and remove Buy Rule column

## Problems fixed

PHP error:

```text
strict_types declaration must be the very first statement
```

This happened because a previous patch inserted a helper before:

```php
declare(strict_types=1);
```

Also, the market table still showed the physical `Budget only` column.

## Apply

```bash
cd /home/luca/Documenti/html/icaro-ops
unzip -o /home/luca/Scaricati/icaro-ops-fix-model-detail-strict-and-buy-rule-column-patch.zip

python3 docs/patch_fix_model_detail_strict_and_buy_rule_column.py

php -l api/public/fleet/model-detail.php
node --check src/js/aircraft-market-remove-buy-rule-column.js
node --check src/js/fleet.js
node --check src/js/fleet-market-table-dialog.js
```

Refresh:

```text
Ctrl + F5
```

## What it does

```text
- moves declare(strict_types=1) immediately after <?php
- makes model-detail.php accept modelId as well as id
- adds a small runtime script that removes the physical Budget only column from the market table
```

## If Details still fails

Run:

```bash
sed -n '1,120p' api/public/fleet/model-detail.php
```

and send the output.
