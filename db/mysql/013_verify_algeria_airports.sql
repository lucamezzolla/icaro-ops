-- Algeria airport import verification queries.

USE icaro_ops;

SELECT
  service_category,
  COUNT(*) AS airport_count
FROM airports
WHERE country_id = (
  SELECT id FROM countries WHERE name = 'Algeria' AND world_region_code = 'AFRICA'
)
GROUP BY service_category
ORDER BY service_category;

SELECT
  icao_code,
  iata_code,
  name,
  city,
  subdivision_name,
  latitude,
  longitude,
  service_category,
  is_commercial,
  is_military,
  is_closed
FROM airports
WHERE country_id = (
  SELECT id FROM countries WHERE name = 'Algeria' AND world_region_code = 'AFRICA'
)
ORDER BY service_category, city, icao_code;
