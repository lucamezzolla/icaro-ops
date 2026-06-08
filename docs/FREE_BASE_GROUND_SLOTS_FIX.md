# Free base ground slots fallback

This patch fixes the dashboard row:

```text
Free base ground slots
```

when the label is present but the value is blank.

## Why

The backend/base data already has enough information:

```text
On ground at current base = 1 / 4
```

So even if `free_ground_aircraft_slots` is missing/empty in one UI path, the UI can safely compute:

```text
4 - 1 = 3
```

## Apply

From the project root:

```bash
unzip -o /home/luca/Scaricati/icaro-ops-free-base-ground-slots-patch.zip
python3 docs/patch_free_base_ground_slots.py

node --check src/js/dashboard-map.js
```

Then hard-refresh the dashboard/map page.

## Rollback

```bash
git restore src/js/dashboard-map.js
rm -f docs/patch_free_base_ground_slots.py docs/FREE_BASE_GROUND_SLOTS_FIX.md
```

## Commit

```bash
git add src/js/dashboard-map.js docs/patch_free_base_ground_slots.py docs/FREE_BASE_GROUND_SLOTS_FIX.md
git commit -m "Fix free base ground slots display"
git push origin development
```
