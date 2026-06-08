# Aircraft market filters force inline

This patch restores the Buy new aircraft filters directly inside `fleet-market-table-dialog.js`.

It uses `aircraft_models.engine_type` as the only source for the Engine filter.

Supported values:

- `TURBOFAN`
- `TURBOPROP`
- `PISTON`
- `TURBOSHAFT`
- `SUPERSONIC`

The legacy `aircraft-market-filters.js` file is made passive to avoid duplicate DOM mutations.
