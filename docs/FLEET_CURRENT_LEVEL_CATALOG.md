# Fleet current-level catalog table

This patch changes the Buy Aircraft dialog.

## Behavior

The buy dialog now shows only aircraft available for the current company/base level.

For the current early-game fallback level, only this starter aircraft is shown:

```text
C208B_GRAND_CARAVAN_EX
```

Endgame or locked aircraft such as Concorde are not shown.

## Files

```text
api/public/fleet/catalog.php
api/public/fleet/model-detail.php
docs/patch_fleet_current_level_catalog.py
docs/fleet_catalog_css_append.css
docs/FLEET_CURRENT_LEVEL_CATALOG.md
```

## Apply

```bash
cd /home/luca/Documenti/html/icaro-ops
unzip -o /home/luca/Scaricati/icaro-ops-fleet-level-catalog-table-patch.zip
python3 docs/patch_fleet_current_level_catalog.py
cat docs/fleet_catalog_css_append.css >> src/css/fleet.css
```

Then refresh:

```text
Ctrl + F5
```

## UI

Buy Aircraft dialog:

```text
table of currently unlocked aircraft
Details button
Buy button
```

Details dialog:

```text
aircraft image
identity
capacity
performance
economics
unlock note
```

## Future progression

Later, replace the fallback starter list with DB-driven unlock rules, for example:

```text
company_level
aircraft_unlock_tier
base/airport aircraft class
reputation
fleet size
license availability
```
