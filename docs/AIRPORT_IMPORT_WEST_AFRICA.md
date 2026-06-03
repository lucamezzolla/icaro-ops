# West Africa airport import batch

This patch imports airports for:

- The Gambia
- Benin
- Burkina Faso
- Cape Verde
- Ghana
- Ivory Coast

## Compact model

No new fields were added to `airports`.

Runway data from Banjul and Burkina Faso is stored in `airport_runway_source_notes`.

## Imported rows

{'The Gambia': 1, 'Benin': 9, 'Burkina Faso': 38, 'Cape Verde': 11, 'Ghana': 14, 'Ivory Coast': 26}

Total imported rows: 99

Expected total airport count if current DB is 1231:

```text
1231 + 99 = 1330
```

## Coordinates

Rows with coordinates:

{'The Gambia': 1, 'Benin': 9, 'Burkina Faso': 38, 'Cape Verde': 11}

## Skipped rows without ICAO

{'Ivory Coast': 1}

Rows without ICAO are intentionally skipped because `airports.icao_code` is the primary key.

## Apply

```bash
cd /home/luca/Documenti/html/icaro-ops
sudo mysql icaro_ops < db/mysql/999_apply_west_africa_airports_patch.sql
```
