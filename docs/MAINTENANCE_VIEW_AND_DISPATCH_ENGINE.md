# Maintenance view and dispatch engine foundation

This patch adds two big foundations:

```text
1. aircraft maintenance page
2. route dispatch engine with backup aircraft logic
```

## Apply

```bash
cd /home/luca/Documenti/html/icaro-ops
unzip -o /home/luca/Scaricati/icaro-ops-maintenance-dispatch-engine-patch.zip
sudo mysql icaro_ops < db/mysql/080_maintenance_view_dispatch_engine.sql
```

## Fleet button

Add the Maintenance button to `src/js/fleet.js` manually or with this command:

```bash
python3 - <<'PY'
from pathlib import Path

path = Path("src/js/fleet.js")
text = path.read_text(encoding="utf-8")

if 'maintenance.html?aircraftId=' not in text:
    text = text.replace(
        '${aircraftImageButton(row)}',
        '${aircraftImageButton(row)}\\n              <a class="secondary aircraft-image-button" href="maintenance.html?aircraftId=${row.company_aircraft_id}">Maintenance</a>',
        1
    )
    path.write_text(text, encoding="utf-8")
    print("OK: added Maintenance link to owned aircraft rows")
else:
    print("SKIP: Maintenance link already present")
PY
```

## Open maintenance page

```text
http://127.0.0.1:8080/maintenance.html?aircraftId=1
```

The API checks ownership using the PHP session.

## Dispatch engine

New endpoint:

```text
api/public/dispatch/process-due-routes.php
```

POST body for development:

```json
{
  "window_minutes": 60,
  "dev_force_due": true
}
```

It will:

```text
- process active routes
- complete due flights first
- try assigned aircraft
- if unavailable, try backup compatible aircraft at origin
- if no aircraft, create mailbox message and apply penalties
```

## Future automation

Later this endpoint can be called by:

```text
- cron
- systemd timer
- web request on login
- background worker
```

## Game design

A route is not a single manual action anymore. A route is a promise.

If the aircraft is not at the origin at departure time:

```text
1. dispatch tries backup aircraft
2. if backup exists: flight starts with backup
3. if no backup: mailbox DISPATCH_BLOCKED
4. company may receive reputation/budget penalty
```

This rewards having reserve aircraft and proper maintenance planning.
