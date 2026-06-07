# Remove physical BUY RULE column and fix Details id

## Apply

```bash
cd /home/luca/Documenti/html/icaro-ops
unzip -o /home/luca/Scaricati/icaro-ops-remove-buy-rule-column-and-fix-details-id-patch.zip

python3 docs/patch_remove_buy_rule_column_and_fix_details_id.py

node --check src/js/fleet.js
node --check src/js/fleet-market-table-dialog.js
node --check src/js/aircraft-market-filters.js
```

Refresh:

```text
Ctrl + F5
```

## What this fixes

```text
- removes the physical BUY RULE / Budget only column
- keeps backend budget validation untouched
- adds aircraft_model_id to fleet PHP list APIs when missing
- makes Details button fall back to model_code / ICAO when id is missing
```

## If Details still fails

Run:

```bash
grep -R "INVALID_MODEL_ID\|function showAircraftDetail\|model-by\|detail.php\|aircraft_model_id" -n api/public/fleet src/js/fleet-market-table-dialog.js src/js/fleet.js
```

and send the output.
