# North Africa airport import

This patch imports airports for:

- Egypt
- Libya
- Morocco
- Sudan
- Tunisia
- Western Sahara

## Compact airport model

No large field expansion was done.

The patch reuses existing fields and adds only the compact source/game fields already introduced with the Algeria import:

- `service_category`
- `aip_url`
- `chart_url`
- `source_rating_percent`

It also adds a separate table for alternative ICAO codes:

- `airport_icao_aliases`

This keeps `airports` compact while preserving cases such as Western Sahara, where the source lists dual ICAO codes.

## Coordinates

Egypt and Libya source tables in the provided PDFs do not include coordinate columns, so their airports are imported with `latitude = NULL` and `longitude = NULL`.

Morocco, Tunisia and Western Sahara include coordinates and are imported with decimal latitude/longitude.

Sudan source table in the provided PDF does not include coordinates in the airport table, so airports are imported without coordinates.

## Imported rows

- Egypt: 29 imported rows, 0 with coordinates
- Libya: 19 imported rows, 0 with coordinates
- Morocco: 33 imported rows, 33 with coordinates
- Sudan: 29 imported rows, 0 with coordinates
- Tunisia: 13 imported rows, 13 with coordinates
- Western Sahara: 3 imported rows, 3 with coordinates

Total imported rows in this patch: 126

## Skipped rows

Rows without ICAO code are intentionally skipped because `airports.icao_code` is the primary key.

## Install

```bash
cd /home/luca/Documenti/html/icaro-ops
sudo mysql icaro_ops < db/mysql/999_apply_north_africa_airports_patch.sql
```

## Verification

```sql
SELECT
  c.name AS country_name,
  a.service_category,
  COUNT(*) AS airport_count
FROM airports a
JOIN countries c ON c.id = a.country_id
WHERE c.name IN ('Egypt', 'Libya', 'Morocco', 'Sudan', 'Tunisia', 'Western Sahara')
  AND c.world_region_code = 'AFRICA'
GROUP BY c.name, a.service_category
ORDER BY c.name, a.service_category;
```
