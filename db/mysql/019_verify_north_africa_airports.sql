-- North Africa airport import verification.

USE icaro_ops;

SELECT
  c.name AS country_name,
  a.service_category,
  COUNT(*) AS airport_count
FROM airports a
JOIN countries c
  ON c.id = a.country_id
WHERE c.name IN ('Egypt', 'Libya', 'Morocco', 'Sudan', 'Tunisia', 'Western Sahara')
  AND c.world_region_code = 'AFRICA'
GROUP BY c.name, a.service_category
ORDER BY c.name, a.service_category;

SELECT
  c.name AS country_name,
  COUNT(*) AS total_airports,
  SUM(CASE WHEN a.latitude IS NOT NULL AND a.longitude IS NOT NULL THEN 1 ELSE 0 END) AS airports_with_coordinates,
  SUM(CASE WHEN a.is_closed THEN 1 ELSE 0 END) AS closed_airports
FROM airports a
JOIN countries c
  ON c.id = a.country_id
WHERE c.name IN ('Egypt', 'Libya', 'Morocco', 'Sudan', 'Tunisia', 'Western Sahara')
  AND c.world_region_code = 'AFRICA'
GROUP BY c.name
ORDER BY c.name;

SELECT
  airport_icao_code,
  alias_icao_code,
  notes
FROM airport_icao_aliases
ORDER BY airport_icao_code, alias_icao_code;
