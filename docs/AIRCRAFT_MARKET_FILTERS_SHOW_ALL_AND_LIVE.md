# Aircraft market filters show all and live filtering

This patch changes the Buy new aircraft market behavior.

## Changes

- The market table is populated immediately with all aircraft.
- Filters run client-side on the already-loaded table rows.
- Changing combo boxes or text inputs immediately refreshes visible rows.
- Clearing filters shows all aircraft again.
- `Engine: Jet` includes both `TURBOFAN` and `TURBOJET`.
- Family options are populated from the real `aircraft_family` values returned by the catalog API.
- Filter logic is scoped only to `#buyAircraftDialog`, so the Fleet table is not touched.
