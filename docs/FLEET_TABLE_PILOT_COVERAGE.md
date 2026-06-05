# Fleet table and pilot coverage wording

This patch redesigns Fleet to match the Staff / Routes / Flight Log pattern.

## Files

```text
fleet.html
src/css/fleet.css
src/js/fleet.js
api/public/fleet/my-aircraft.php
api/public/fleet/detail.php
api/public/fleet/catalog.php
docs/FLEET_TABLE_PILOT_COVERAGE.md
```

## Apply

```bash
cd /home/luca/Documenti/html/icaro-ops
unzip -o /home/luca/Scaricati/icaro-ops-fleet-table-pilot-coverage-patch.zip
```

## Important database note

`api/public/fleet/catalog.php` expects `aircraft_models.base_purchase_price`.

If your table uses a different price column, edit this line in `catalog.php`:

```sql
base_purchase_price AS new_purchase_price
```

and replace it with your real catalog price column.

## Business rule

Pilots are not bound to individual aircraft.

The rule is now expressed as:

```text
qualified pilot pool coverage
```

Example:

```text
2 Cessna 208B aircraft require 4 active C208-qualified pilots.
The pilots are a pool and can be dispatched across compatible aircraft.
```

## Fleet UI

Owned aircraft table:

```text
Registration
Aircraft
Status
Airport
Condition
Hours
Cycles
Actions
```

Details dialog:

```text
identity
status
performance
financials
recent flights
pilot coverage explanation
```

Buy dialog:

```text
catalog cards
pilot coverage message
clear 409 warnings when coverage is insufficient
```
