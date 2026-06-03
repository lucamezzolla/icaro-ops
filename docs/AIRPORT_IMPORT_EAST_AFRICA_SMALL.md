# East Africa / Indian Ocean small airport import batch

This patch imports airports for:

- Burundi
- Djibouti
- Eritrea
- British Indian Ocean Territory
- Comoros

## Compact model

No new columns were added to `airports`.

The Burundi PDF includes runway text, but instead of expanding `airports`, the patch stores raw runway notes in a separate table:

- `airport_runway_source_notes`

This keeps the main airport table compact and leaves room for a future normalized runway model.

## Coordinates

Only Burundi includes coordinates in the uploaded PDF table, so only Burundi airports are imported with decimal latitude/longitude.

Djibouti, Eritrea, British Indian Ocean Territory and Comoros do not include coordinates in the provided PDF tables, so those rows use `NULL` coordinates.

## Imported rows

- Burundi: 4 imported rows, 4 with coordinates
- Djibouti: 9 imported rows, 0 with coordinates
- Eritrea: 6 imported rows, 0 with coordinates
- British Indian Ocean Territory: 1 imported rows, 0 with coordinates
- Comoros: 4 imported rows, 0 with coordinates

Total imported rows in this patch: 24

## Install

```bash
cd /home/luca/Documenti/html/icaro-ops
sudo mysql icaro_ops < db/mysql/999_apply_east_africa_small_airports_patch.sql
```

## Verification

```sql
SELECT
  c.name AS country_name,
  COUNT(*) AS total_airports,
  SUM(CASE WHEN a.latitude IS NOT NULL AND a.longitude IS NOT NULL THEN 1 ELSE 0 END) AS airports_with_coordinates
FROM airports a
JOIN countries c ON c.id = a.country_id
WHERE c.name IN ('Burundi', 'Djibouti', 'Eritrea', 'British Indian Ocean Territory', 'Comoros')
GROUP BY c.name
ORDER BY c.name;
```
