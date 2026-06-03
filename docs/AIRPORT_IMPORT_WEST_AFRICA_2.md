# West Africa 2 airport import batch

This patch imports airports for:

- Guinea
- Guinea-Bissau
- Liberia
- Mali
- Mauritania
- Niger

## Compact model

No new fields were added to `airports`.

This patch uses a temporary table and `JOIN countries` / `JOIN icao_prefixes`, so missing country-name matches are reported as diagnostics instead of causing `country_id` NULL failures.

## Imported rows

{'Guinea': 15, 'Guinea-Bissau': 5, 'Liberia': 10, 'Mali': 25, 'Mauritania': 21, 'Niger': 20}

Total imported rows: 96

Expected total airport count if current DB is 1330:

```text
1330 + 96 = 1426
```

## Coordinates

Only Guinea-Bissau has coordinates in the provided table; 5 coordinate pairs are imported.

Rows with source coordinates:

{'Guinea-Bissau': 5}

## Skipped rows without valid ICAO

{'Guinea-Bissau': 1, 'Liberia': 1, 'Mali': 1, 'Niger': 1}

Details:

- Guinea-Bissau: Quebo / Quebo Airport (missing_or_invalid_icao)
- Liberia: Foya / Foya Airport (missing_or_invalid_icao)
- Mali: Manantali / Bengassi Airport (missing_or_invalid_icao)
- Niger: N'Gourti / Jaouro Airport (missing_or_invalid_icao)

## Apply

```bash
cd /home/luca/Documenti/html/icaro-ops
sudo mysql icaro_ops < db/mysql/999_apply_west_africa_2_airports_patch.sql
```
