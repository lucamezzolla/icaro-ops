# Aircraft market filters based on real DB fields

This patch makes the Buy new aircraft dialog filters use real catalog fields instead of visible table text.

## Changes

- `api/public/fleet/catalog.php` now returns `aircraft_family`, `engine_type`, and `aircraft_category`.
- `src/js/fleet-market-table-dialog.js` writes those values as row `data-*` attributes.
- `src/js/aircraft-market-filters.js` filters against the row data attributes.
- Engine filter groups `Jet` as `TURBOFAN + TURBOJET`.
- Family filter options are generated dynamically from the loaded catalog rows.
- The market table still starts empty until at least one filter is selected.

## Expected behavior

After normalizing the DB with `119_normalize_aircraft_engine_and_family.sql`:

- Engine `Jet` shows aircraft with `TURBOFAN` or `TURBOJET`, including A320/737/Concorde-like entries where present.
- Engine `Turboprop` shows `TURBOPROP`.
- Engine `Piston` shows `PISTON`.
- Engine `Helicopter` shows `TURBOSHAFT`.
- Family filter uses normalized values such as `B737_FAMILY`, `A320_FAMILY`, `MD80_FAMILY`.
