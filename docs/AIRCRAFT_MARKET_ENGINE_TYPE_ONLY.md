# Aircraft market engine type only

This patch aligns the Buy new aircraft filters with the database cleanup.

## Database

Migration `120_remove_aircraft_family_category_and_fix_engine_filter.sql`:

- sets Concorde rows to `engine_type = SUPERSONIC`;
- removes `aircraft_family` from `aircraft_models` if present;
- removes `aircraft_category` from `aircraft_models` if present.

## Frontend/API

- `catalog.php` no longer selects removed columns.
- The market row dataset uses `engine_type` as the only engine filter source.
- The Family filter is removed.
- The Engine filter contains Jet, Turbofan, Turbojet, Turboprop, Piston, Turboshaft/helicopter, and Supersonic.
- `Engine: Jet` matches `TURBOFAN`, `TURBOJET`, and legacy `JET` values.
- `Engine: Supersonic` matches `SUPERSONIC`.
