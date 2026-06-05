# Routes / Services visual separation

This patch makes the Routes page reflect the new architecture.

## What changes

The page now lists:

```text
scheduled_services
```

joined with:

```text
air_routes
```

A created item is now:

```text
Scheduled Service over an Abstract Air Route
```

not a real flight.

## Layers

```text
Air Route
  LIRA -> LIRZ
  abstract route, market/scope/distance/required class

Scheduled Service
  Daily at 10:00 UTC
  base ticket, required aircraft class, preferred model

Flight Instance
  real operational flight
  aircraft/staff/passengers/costs/dispatch/backup
```

## Apply

```bash
cd /home/luca/Documenti/html/icaro-ops
unzip -o /home/luca/Scaricati/icaro-ops-routes-services-separation-patch.zip
python3 docs/patch_routes_html_services_wording.py
```

Refresh:

```text
Ctrl + F5
```

## Next patch

Wire service start/generation to create a real flight instance and dispatch a compatible aircraft.
