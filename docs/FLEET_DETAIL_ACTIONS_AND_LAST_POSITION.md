# Fleet detail actions and last position

This patch keeps the Fleet table compact by leaving only the Details action in each owned-aircraft row.

Changes:

- Renames the owned Fleet table header from `Airport` / `Airports` to `Last position`.
- Shows `In flight` in the Last position column when an aircraft status is `IN_FLIGHT`.
- Removes `Image` and `Maintenance` actions from the Fleet table row.
- Adds `Image` and `Maintenance` actions inside the aircraft detail dialog, before the dialog close area.

Notes:

`Cycles` means aircraft operating cycles. In aviation and maintenance planning, a cycle usually means one complete takeoff/landing operational cycle. It is useful because some components age more by repeated takeoff/landing/pressurization cycles than by flight hours alone.
