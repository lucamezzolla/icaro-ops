# Dashboard capacity labels clarification

This patch fixes misleading labels in the company/dashboard panel.

## Problem

The panel mixed global company values and current-base capacity values:

```text
Aircraft 4 / 6
At base 1 / 4
In flight 4
Maintenance 0
Free fleet slots 2
Free ground slots 3
```

But the DB confirmed:

```text
Company aircraft total = 8
Company in flight = 4
Current base LIRA managed aircraft = 4 / 6
Current base on ground = 1 / 4
```

So `Aircraft 4 / 6` was not global company aircraft; it was current-base managed capacity.

## UI labels after patch

```text
Base managed aircraft
On ground at current base
Company aircraft in flight
Company aircraft in maintenance
Free base fleet slots
Free base ground slots
```

The patch also prefers global `data.aircraft_in_flight_count` over base-scoped `capacity.aircraft_in_flight_count` when both exist.

## Apply

From the project root:

```bash
unzip -o /home/luca/Scaricati/icaro-ops-dashboard-capacity-labels-patch.zip
python3 docs/patch_dashboard_capacity_labels.py

node --check src/js/dashboard-map.js
```

Then hard-refresh the dashboard/map page.

## Rollback

```bash
git restore src/js/dashboard-map.js
rm -f docs/patch_dashboard_capacity_labels.py docs/DASHBOARD_CAPACITY_LABELS_FIX.md
```

## Commit

```bash
git add src/js/dashboard-map.js docs/patch_dashboard_capacity_labels.py docs/DASHBOARD_CAPACITY_LABELS_FIX.md
git commit -m "Clarify dashboard fleet capacity labels"
git push origin development
```
