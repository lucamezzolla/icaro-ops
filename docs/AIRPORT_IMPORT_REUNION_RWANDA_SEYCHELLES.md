# Réunion, Rwanda and Seychelles airport import batch

This patch imports airports for:

- Réunion
- Rwanda
- Seychelles

## Compact model

No new fields were added to `airports`.

The patch uses existing fields:

- `icao_code`
- `icao_prefix`
- `iata_code`
- `name`
- `city`
- `location_name`
- `subdivision_name`
- `latitude`
- `longitude`
- `airport_type`
- `service_category`

For Réunion, the source table has a `Usage` column. It is stored in `location_name` for now to avoid adding a new field to `airports`.

## Coordinates

- Réunion: no coordinates in the provided table.
- Rwanda: coordinates are present and imported.
- Seychelles: no coordinates in the provided table.

## Imported rows

- Réunion: 2 imported rows, 0 with coordinates
- Rwanda: 6 imported rows, 6 with coordinates
- Seychelles: 15 imported rows, 0 with coordinates

Total imported rows in this patch: 23

## Skipped rows

Rows without ICAO are intentionally skipped because `airports.icao_code` is the primary key.

- Rwanda: Nyamata / Bugesera International Airport (missing_or_invalid_icao)

## Install

```bash
cd /home/luca/Documenti/html/icaro-ops
sudo mysql icaro_ops < db/mysql/999_apply_reunion_rwanda_seychelles_airports_patch.sql
```

## Verification

```sql
SELECT
  c.name AS country_name,
  COUNT(*) AS total_airports,
  SUM(CASE WHEN a.latitude IS NOT NULL AND a.longitude IS NOT NULL THEN 1 ELSE 0 END) AS airports_with_coordinates
FROM airports a
JOIN countries c ON c.id = a.country_id
WHERE c.name IN ('Réunion', 'Rwanda', 'Seychelles')
GROUP BY c.name
ORDER BY c.name;
```
