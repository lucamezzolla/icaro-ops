# Menu Flights label and scheduled time toggle fix

## Apply

```bash
cd /home/luca/Documenti/html/icaro-ops
unzip -o /home/luca/Scaricati/icaro-ops-menu-flights-scheduled-time-fix-patch.zip

python3 docs/patch_all_menus_routes_to_flights.py
python3 docs/patch_routes_scheduled_time_toggle.py
python3 docs/patch_routes_html_flights_defaults.py
```

Refresh:

```text
Ctrl + F5
```

## Fixes

- Every page menu label changes from `Routes` to `Flights`.
- Create dialog defaults to `On demand / non-scheduled`.
- When selecting `Scheduled`, the scheduled time input is re-enabled and gets `10:00`.
- When selecting `On demand`, the scheduled time is cleared and disabled.
