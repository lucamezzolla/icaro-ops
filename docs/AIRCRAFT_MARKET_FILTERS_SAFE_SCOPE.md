# Aircraft market filters safe scope

This patch makes the Buy new aircraft filters safe for the Fleet page.

## Why

The previous filter script could run against the page too broadly and could fail or interfere with Fleet initialization.

## Changes

- The filter logic now runs only inside `#buyAircraftDialog`.
- It no longer scans every table on the Fleet page.
- It handles `#aircraftMarketTableBody` correctly when the container itself is a `<tbody>`.
- Errors are caught and logged instead of blocking the Fleet page.
- The market still starts empty until at least one filter is selected.
- `Engine: Jet` still includes `TURBOFAN` and `TURBOJET`.
