# Fleet toolbar plus and refresh icons

Moves the aircraft purchase action from the page header to the table toolbar.

Changes:

- Removes the top `Buy aircraft` / `New airplane` button.
- Adds a compact `+` button next to refresh above the Fleet table.
- Changes `Refresh` text to the circular arrow icon `↻`.
- Keeps the existing JavaScript binding through `id="buyAircraftButton"` and `id="refreshButton"`.
- Aligns the toolbar to the right.

Apply from project root:

```bash
python3 docs/patch_fleet_toolbar_plus_refresh_icons.py
```
