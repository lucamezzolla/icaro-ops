# Buy aircraft dialog filters in active Fleet dialog

This patch fixes the `Buy new aircraft` dialog filters by patching the active dialog implementation in `src/js/fleet.js`.

The current Fleet page opens `#buyAircraftDialog` through `openBuyDialog()` in `fleet.js`, not through `fleet-market-table-dialog.js`. Previous patches added filters to the unused/secondary dialog path, so the visible dialog did not show them.

The patched catalog view:

- shows all aircraft immediately;
- adds ICAO, Search, Max price, Min pax, Max pax and Engine filters;
- filters live on input/change;
- uses `aircraft_models.engine_type` values exactly:
  - `TURBOFAN`
  - `TURBOPROP`
  - `PISTON`
  - `TURBOSHAFT`
  - `SUPERSONIC`
- does not use the obsolete `JET` value.
