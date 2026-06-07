# Fleet toolbar top-right

Moves the compact Fleet actions (`+` and `↻`) back to the top-right page header, where the old `New airplane` / `Buy aircraft` button used to be.

The patch preserves the existing button ids:

- `buyAircraftButton`
- `refreshButton`

So the current JavaScript listeners keep working.

Apply from the project root:

```bash
python3 docs/patch_fleet_toolbar_top_right.py
node --check src/js/fleet.js
```
