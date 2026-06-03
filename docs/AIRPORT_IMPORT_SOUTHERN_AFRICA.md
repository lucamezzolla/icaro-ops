# Southern Africa airport import batch

This patch imports airports for:

- Botswana
- Eswatini
- Lesotho
- Namibia
- South Africa

## Compact model

No new fields were added to `airports`.

Runway data from Eswatini and selected Botswana rows is stored in `airport_runway_source_notes`.

## Imported rows

{'Botswana': 36, 'Eswatini': 13, 'Lesotho': 32, 'Namibia': 33, 'South Africa': 110}

Total imported rows: 224

Expected total airport count if current DB is 1007:

```text
1007 + 224 = 1231
```

## Coordinates

Rows with coordinates:

{'Botswana': 36, 'Eswatini': 13, 'South Africa': 108}

## Skipped rows without ICAO

{'Botswana': 1, 'Eswatini': 1, 'Lesotho': 1}

Rows without ICAO, `none`, or `ident` are intentionally skipped because `airports.icao_code` is the primary key.

For South Africa, this patch imports the clean ICAO rows extracted from the provided PDF table. Rows whose ICAO field was not a clean ICAO code are skipped for now.

## Apply

```bash
cd /home/luca/Documenti/html/icaro-ops
sudo mysql icaro_ops < db/mysql/999_apply_southern_africa_airports_patch.sql
```
