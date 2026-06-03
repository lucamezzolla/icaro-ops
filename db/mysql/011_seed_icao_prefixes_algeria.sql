-- ICAO prefix seed for Algeria.

USE icaro_ops;

INSERT INTO icao_prefixes (
  prefix,
  country_id,
  area_name,
  notes
)
SELECT
  'DA',
  c.id,
  'Algeria',
  'ICAO prefix for Algeria airport imports.'
FROM countries c
WHERE c.name = 'Algeria'
  AND c.world_region_code = 'AFRICA'
ON DUPLICATE KEY UPDATE
  country_id = VALUES(country_id),
  area_name = VALUES(area_name),
  notes = VALUES(notes),
  is_active = TRUE;
