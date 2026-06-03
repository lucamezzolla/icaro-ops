# East Africa / Indian Ocean airport import batch

This patch imports airports for:

- Ethiopia
- Kenya
- Madagascar
- Malawi
- Mauritius
- Mayotte
- Mozambique

## Compact model

No new fields were added to `airports`.

The patch uses existing fields:

- `icao_code`
- `icao_prefix`
- `iata_code`
- `name`
- `city`
- `subdivision_name`
- `latitude`
- `longitude`
- `elevation_ft`
- `airport_type`
- `service_category`
- `is_commercial`
- `is_military`
- `is_closed`

## Coordinates and elevation

- Ethiopia: no coordinates in the provided table.
- Kenya: coordinates and elevation are present for many rows.
- Madagascar: coordinates are present for rows with ICAO.
- Malawi: no coordinates in the provided table.
- Mauritius: coordinates are present.
- Mayotte: no coordinates in the provided table.
- Mozambique: coordinates are present for rows with ICAO.

## Imported rows

- Ethiopia: 45 imported rows, 0 with coordinates, 0 with elevation
- Kenya: 60 imported rows, 56 with coordinates, 53 with elevation
- Madagascar: 62 imported rows, 62 with coordinates, 0 with elevation
- Malawi: 22 imported rows, 0 with coordinates, 0 with elevation
- Mauritius: 3 imported rows, 3 with coordinates, 0 with elevation
- Mayotte: 1 imported rows, 0 with coordinates, 0 with elevation
- Mozambique: 23 imported rows, 23 with coordinates, 0 with elevation

Total imported rows in this patch: 216

## Skipped rows

Rows without ICAO are intentionally skipped because `airports.icao_code` is the primary key.

- Ethiopia: Dolo / Dolo Airport (missing_icao_in_source)
- Ethiopia: Shire / Shire Airport (missing_icao_in_source)
- Ethiopia: Bishoftu/Addis Ababa / Bishoftu International Airport (under_construction_no_icao)
- Kenya: Kiwayu / Kiwayu Airport (missing_icao_in_source)
- Kenya: Lake Baringo / Lake Baringo Airport (missing_icao_in_source)
- Kenya: Liboi / Liboi Airport (missing_icao_in_source)
- Kenya: Kimwarer / Kimwarer Airport (missing_icao_in_source)
- Kenya: Angama Mara / Angama Mara Airport (missing_icao_in_source)
- Kenya: Lewa Downs / Lewa Airport (missing_icao_in_source)
- Kenya: Loitokitok / Loitokitok Airport (missing_icao_in_source)
- Kenya: Tatu City / Tatu City Airstrip (missing_icao_in_source)
- Madagascar: Andavadoaka / Andavadoaka Airport (missing_icao_in_source)
- Madagascar: Bealanana / Ankaizina Airport (missing_icao_in_source)
- Madagascar: Doany / Doany Airport (missing_icao_in_source)
- Mozambique: Bazaruto Island / Bazaruto Island Airport (missing_icao_in_source)
- Mozambique: Benguerra Island / Benguerra Island Airport (missing_icao_in_source)
- Mozambique: Indigo Bay, Bazaruto Island / Indigo Bay Lodge Airport (missing_icao_in_source)

## Install

```bash
cd /home/luca/Documenti/html/icaro-ops
sudo mysql icaro_ops < db/mysql/999_apply_east_africa_airports_patch.sql
```

## Verification

```sql
SELECT
  c.name AS country_name,
  COUNT(*) AS total_airports,
  SUM(CASE WHEN a.latitude IS NOT NULL AND a.longitude IS NOT NULL THEN 1 ELSE 0 END) AS airports_with_coordinates,
  SUM(CASE WHEN a.elevation_ft IS NOT NULL THEN 1 ELSE 0 END) AS airports_with_elevation
FROM airports a
JOIN countries c ON c.id = a.country_id
WHERE c.name IN ('Ethiopia', 'Kenya', 'Madagascar', 'Malawi', 'Mauritius', 'Mayotte', 'Mozambique')
GROUP BY c.name
ORDER BY c.name;
```
