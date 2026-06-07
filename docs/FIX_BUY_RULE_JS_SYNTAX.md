# Fix BUY RULE JS syntax

## Problem

The previous cleanup removed the literal string `BUY RULE` from JavaScript code too, producing invalid syntax:

```js
header.textContent.trim().toUpperCase() === );
```

## Apply

```bash
cd /home/luca/Documenti/html/icaro-ops
unzip -o /home/luca/Scaricati/icaro-ops-fix-buy-rule-js-syntax-patch.zip

python3 docs/patch_fix_buy_rule_js_syntax.py

node --check src/js/fleet.js
node --check src/js/fleet-market-table-dialog.js
node --check src/js/aircraft-market-filters.js
```

Then refresh:

```text
Ctrl + F5
```

## Expected

All `node --check` commands should return no syntax errors.
