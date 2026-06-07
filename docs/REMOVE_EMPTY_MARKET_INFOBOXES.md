# Remove empty Buy aircraft info boxes

## Apply

```bash
cd /home/luca/Documenti/html/icaro-ops
unzip -o /home/luca/Scaricati/icaro-ops-remove-empty-market-infoboxes-patch.zip

python3 docs/patch_remove_empty_market_infoboxes.py
```

Refresh:

```text
Ctrl + F5
```

## What it removes

Empty blocks like:

```html
<div class="info-box"></div>
<section class="info-box"></section>
```

from:

```text
fleet.html
src/js/fleet.js
src/js/fleet-market-table-dialog.js
```

No replacement text is added.
