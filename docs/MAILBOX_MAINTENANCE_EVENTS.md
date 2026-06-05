# Mailbox, maintenance and aircraft events

This patch adds the first foundation for operations messaging and aircraft reliability.

## What it adds

```text
game_mailbox_messages
aircraft_maintenance_profiles
aircraft_operational_events
v_mailbox_messages
v_aircraft_maintenance_status
```

And UI/API:

```text
mailbox.html
src/js/mailbox.js
src/css/mailbox.css

api/public/mailbox/list.php
api/public/mailbox/mark.php
api/public/maintenance/run-check.php
```

## Apply

```bash
cd /home/luca/Documenti/html/icaro-ops
unzip -o /home/luca/Scaricati/icaro-ops-mailbox-maintenance-patch.zip
sudo mysql icaro_ops < db/mysql/078_mailbox_maintenance_events.sql
```

## Open

```text
http://127.0.0.1:8080/mailbox.html
```

## Add nav link

```bash
python3 - <<'PY'
from pathlib import Path

for filename in ["index.html", "fleet.html", "staff.html", "routes.html"]:
    path = Path(filename)
    if not path.exists():
        continue
    text = path.read_text(encoding="utf-8")
    if 'href="mailbox.html"' not in text:
        text = text.replace(
            '<a href="#">Finance</a>',
            '<a href="mailbox.html">Mailbox</a>\\n          <a href="#">Finance</a>',
            1
        )
        path.write_text(text, encoding="utf-8")
        print(f"OK: added Mailbox nav to {filename}")
    else:
        print(f"SKIP: Mailbox nav already present in {filename}")
PY
```

## Design direction

Future automatic maintenance flow:

```text
1. Flight completes
2. Aircraft condition decreases based on model profile
3. Cycles/hours increase
4. Fault risk is evaluated
5. If threshold/risk triggers:
   - event is stored
   - mailbox message is created
   - aircraft may become MAINTENANCE or remain AVAILABLE with warning
```

Future mailbox actions:

```text
- schedule maintenance
- substitute aircraft
- delay flight
- cancel flight
```

Canceling flights should reduce reputation and/or budget.
