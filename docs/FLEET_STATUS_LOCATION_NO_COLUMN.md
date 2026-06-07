# Fleet status location without separate column

This patch removes the physical `Last position` / `Airport` column from the owned aircraft table.

The current aircraft position is now displayed inside the status badge:

- `AVAILABLE (LIRF)`
- `PARKED (LIRA)`
- `MAINTENANCE (LPPT)`
- `IN_FLIGHT (In flight)`

The patch also preserves a legacy `displayAircraftAirport()` helper so older code paths remain safe.
