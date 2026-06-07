# Fleet badge full width and IN FLIGHT label

This patch keeps the Fleet table compact and improves the status badge rendering:

- The status badge fills the whole Status column width.
- `IN_FLIGHT` is displayed as `IN FLIGHT`.
- In-flight aircraft do not show an airport in parentheses.
- Available/parked/maintenance aircraft can still show the current airport, for example `AVAILABLE (LIRF)`.
- The old separate airport/last-position column is removed if it is still present.
