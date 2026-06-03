# East / Southern Africa airport import batch

This patch imports airports for:

- Somalia
- South Sudan
- Tanzania
- Uganda
- Zambia
- Zimbabwe

## Compact model

No new fields were added to `airports`.

Runway data from Tanzania and Uganda is stored in `airport_runway_source_notes`, outside the main airport table.

## Coordinates

- Somalia: no coordinates in the provided airport table.
- South Sudan: no coordinates in the provided airport table.
- Tanzania: no coordinates in the provided airport table, but runway data is present.
- Uganda: coordinates, elevation and runway data are present for many rows.
- Zambia: no coordinates in the provided airport table.
- Zimbabwe: no coordinates in the provided airport table.

## Imported rows

- Somalia: 17 imported rows, 0 with coordinates, 0 with elevation
- South Sudan: 24 imported rows, 0 with coordinates, 0 with elevation
- Tanzania: 40 imported rows, 0 with coordinates, 0 with elevation
- Uganda: 26 imported rows, 25 with coordinates, 26 with elevation
- Zambia: 23 imported rows, 0 with coordinates, 0 with elevation
- Zimbabwe: 20 imported rows, 0 with coordinates, 0 with elevation

Total imported rows in this patch: 150

## Skipped rows

Rows without ICAO are intentionally skipped because `airports.icao_code` is the primary key.

- Somalia: Abudwak (Caabudwaaq) / Abudwak Airport (Caabudwaaq Airport) (missing_icao_in_source)
- Somalia: Baledogle (wanlaweyn) / Baledogle Airport (missing_icao_in_source)
- Somalia: Dhusamareb (Dhuusamareeb) / Dhusamareb Airport (Ugas Nur Airport) (missing_icao_in_source)
- Somalia: Rage Ele (Rage Ele) / Rage Ele Airport (missing_icao_in_source)
- Somalia: Garbaharey (Garba Harre, Garbahaareey) / Garbaharey Airport (missing_icao_in_source)
- Somalia: Guri'el (Guriel) / Guriel Airport (missing_icao_in_source)
- South Sudan: Adareil / Adareil Airstrip (missing_icao_in_source)
- South Sudan: Duar / Thar Jath Airstrip (missing_icao_in_source)
- Tanzania: Rubondo Island National Park / Rubondo Airstrip (missing_icao_in_source)
- Tanzania: Selous Game Reserve / Mtemere Airstrip (missing_icao_in_source)
- Tanzania: Songo Songo Island / Songo Songo Airstrip (missing_icao_in_source)
- Uganda: Hoima / Kabalega International Airport (missing_icao_in_source)
- Uganda: Kihihi / Savannah Airstrip (missing_icao_in_source)
- Uganda: Matany / Matany Airstrip (missing_icao_in_source)
- Uganda: Moyo / Moyo Airport (missing_icao_in_source)
- Uganda: Chobe Safari Lodge / Chobe Safari Lodge Airport (missing_icao_in_source)
- Uganda: Mutukula / Mutukula Airport (missing_icao_in_source)
- Uganda: Nakasongola / Nakasongola Airport (missing_icao_in_source)
- Uganda: Nebbi / Nebbi Airport (missing_icao_in_source)
- Uganda: Patongo / Patongo Airfield (missing_icao_in_source)
- Uganda: Ishasha River Camp / Ishasha River Camp Airport (missing_icao_in_source)
- Zimbabwe: Mhangura / Mhangura Airport, now closed (missing_icao_in_source)

## Install

```bash
cd /home/luca/Documenti/html/icaro-ops
sudo mysql icaro_ops < db/mysql/999_apply_east_southern_africa_airports_patch.sql
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
WHERE c.name IN ('Somalia', 'South Sudan', 'Tanzania', 'Uganda', 'Zambia', 'Zimbabwe')
GROUP BY c.name
ORDER BY c.name;
```
