# Aircraft market engine filter fix

Fixes the Buy new aircraft market filters so Engine = Jet uses the real `engine_type` value returned by the backend instead of trying to infer the engine from visible table text.

Changes:

- `api/public/fleet/catalog.php` now returns `aircraft_family` and `engine_type`.
- `src/js/fleet-market-table-dialog.js` stores ICAO, family, engine, price and passenger capacity as `data-*` attributes on each aircraft row.
- `src/js/aircraft-market-filters.js` reads those attributes and normalizes common engine values such as `TURBOFAN` and `TURBOJET` to `JET`.

Expected result: selecting Engine = Jet should show jet aircraft such as Boeing 737 and Airbus A320 families when present in the catalog.
