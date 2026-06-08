# Aircraft market engine filter DB values

This patch fixes the Buy new aircraft engine filter after the aircraft model cleanup.

## Rules

- The source of truth is `aircraft_models.engine_type`.
- Market rows store that value in `data-aircraft-engine` and `data-engine-type`.
- The Family filter is removed because `aircraft_family` was removed from the table.
- The Engine filter options are aligned with DB values:
  - Jet -> `TURBOFAN` and legacy `TURBOJET`/`JET`
  - Turbofan -> `TURBOFAN`
  - Turboprop -> `TURBOPROP`
  - Piston -> `PISTON`
  - Turboshaft / helicopter -> `TURBOSHAFT`
  - Supersonic -> `SUPERSONIC`

## Expected checks

```bash
php -l api/public/fleet/catalog.php
node --check src/js/fleet-market-table-dialog.js
node --check src/js/aircraft-market-filters.js
```
