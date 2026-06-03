# Central Africa airport import batch, fixed v10c

This replaces the broken v10/v10b flow.

## Imported rows

- Angola: 46
- Cameroon: 21
- Chad: 21
- Central African Republic: 31

Total imported rows: 119

Expected total airport count if current DB is 588:

```text
588 + 119 = 707
```

## Fix

Runway notes are inserted only with a `JOIN airports`, so missing ICAO references cannot break the foreign key.

## Apply

```bash
cd /home/luca/Documenti/html/icaro-ops
sudo mysql icaro_ops < db/mysql/999_apply_central_africa_airports_patch.sql
```
