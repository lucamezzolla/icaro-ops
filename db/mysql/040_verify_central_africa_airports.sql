USE icaro_ops;

SELECT COUNT(*) AS total_airports
FROM airports;

SELECT
  c.name AS country_name,
  COUNT(*) AS total_airports,
  SUM(CASE WHEN a.latitude IS NOT NULL AND a.longitude IS NOT NULL THEN 1 ELSE 0 END) AS airports_with_coordinates,
  SUM(CASE WHEN a.elevation_ft IS NOT NULL THEN 1 ELSE 0 END) AS airports_with_elevation,
  SUM(CASE WHEN a.is_closed THEN 1 ELSE 0 END) AS closed_airports
FROM airports a
JOIN countries c
  ON c.id = a.country_id
WHERE c.name IN ('Angola', 'Cameroon', 'Chad', 'Central African Republic')
  AND c.world_region_code = 'AFRICA'
GROUP BY c.name
ORDER BY c.name;
