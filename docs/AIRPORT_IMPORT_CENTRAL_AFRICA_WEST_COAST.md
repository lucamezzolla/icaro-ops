# Central Africa west/coast airport import batch

This patch imports airports for:

- Equatorial Guinea
- Gabon
- São Tomé and Príncipe
- Democratic Republic of the Congo
- Republic of the Congo

## Compact model

No new fields were added to `airports`.

## Imported rows

{'Equatorial Guinea': 6, 'Gabon': 29, 'São Tomé and Príncipe': 3, 'Republic of the Congo': 23, 'Democratic Republic of the Congo': 239}

Total imported rows: 300

Expected total airport count if current DB is 707:

```text
707 + 300 = 1007
```

## Coordinates

Rows with coordinates:

{'Equatorial Guinea': 6, 'São Tomé and Príncipe': 3}

## Skipped rows without ICAO

{'Equatorial Guinea': 1, 'Gabon': 4, 'Republic of the Congo': 2, 'Democratic Republic of the Congo': 4}

Rows without ICAO are intentionally skipped because `airports.icao_code` is the primary key.

## Apply

```bash
cd /home/luca/Documenti/html/icaro-ops
sudo mysql icaro_ops < db/mysql/999_apply_central_africa_west_coast_airports_patch.sql
```
