# Short public flight code display

## Problem

The UI displayed the internal technical code:

```text
DOM-0009-C002-OND-ONDEMAND-1780767477
```

The player-facing flight code should be:

```text
DOM-0009
```

The long code remains internal only, to avoid DB unique-key collisions when a cancelled flight is recreated.

## Apply

```bash
cd /home/luca/Documenti/html/icaro-ops
unzip -o /home/luca/Scaricati/icaro-ops-short-flight-code-display-patch.zip

sudo mysql icaro_ops < db/mysql/096_backfill_short_public_flight_codes.sql

python3 docs/patch_routes_api_public_flight_code.py
python3 docs/patch_routes_ui_short_flight_code.py
```

Refresh:

```text
Ctrl + F5
```

## Result

Table and details show:

```text
DOM-0009
```

Details may still show the internal code separately:

```text
DOM-0009-C002-OND-ONDEMAND-1780767477
```
