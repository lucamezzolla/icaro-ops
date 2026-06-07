# Fleet sortable table and detail actions

This patch cleans the Fleet table UX:

- removes the final table column containing the Details button;
- opens aircraft details by clicking the underlined aircraft name;
- keeps the initial table order as provided by the backend, so first purchased aircraft stay first;
- allows manual sorting by every visible Fleet table column;
- moves Image and Maintenance actions to the aircraft detail dialog footer, to the left of Close;
- renders Maintenance as a secondary button instead of an anchor styled as a button;
- keeps IN_FLIGHT displayed as `IN FLIGHT` without underscore or location suffix.

`Cycles` means takeoff/landing cycles. It is different from flight hours: a short hop and a long-haul flight both add one cycle, but add very different airframe hours.
