# Staff / personnel system

This patch introduces the first personnel system.

## What it adds

- Hides/disables current test rival companies so the map focuses on the player's company.
- Creates game-generated staff candidates.
- Adds pilots and technicians.
- Adds personality/risk parameters:
  - fear
  - courage
  - stress tolerance
  - discipline
  - teamwork
  - reliability
  - ambition
  - fatigue risk
- Adds licenses and ratings.
- Adds hired company staff persistence.

## Gameplay assumptions

To dispatch the Cessna 208 for passenger operations later, the game should require:

```text
2 active hired pilots
CPL
C208_TYPE
```

Technicians will become required for maintenance and dispatch reliability.

## Apply

```bash
cd /home/luca/Documenti/html/icaro-ops
unzip -o /home/luca/Scaricati/icaro-ops-staff-personnel-patch.zip
sudo mysql icaro_ops < db/mysql/074_create_staff_personnel.sql
```

## Open

```text
http://127.0.0.1:8080/staff.html
```

## Optional nav links

Add a Staff menu item to dashboard and fleet pages.

```bash
python3 - <<'PY'
from pathlib import Path

for filename in ["index.html", "fleet.html"]:
    path = Path(filename)
    text = path.read_text(encoding="utf-8")
    if 'href="staff.html"' not in text:
        text = text.replace('<a href="#">Offers</a>', '<a href="staff.html">Staff</a>\\n          <a href="#">Offers</a>', 1)
        path.write_text(text, encoding="utf-8")
        print(f"OK: added Staff nav to {filename}")
    else:
        print(f"SKIP: Staff nav already present in {filename}")
PY
```

## Test

```bash
curl "http://127.0.0.1:8080/api/public/staff/candidates.php"
curl "http://127.0.0.1:8080/api/public/staff/my-staff.php"
```

Both require an authenticated PHP session.
