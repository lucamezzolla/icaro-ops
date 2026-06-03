USE icaro_ops;

INSERT INTO icao_prefixes (
  prefix,
  country_id,
  area_name,
  notes
) VALUES
('FE', (SELECT id FROM countries WHERE name = 'Central African Republic' AND world_region_code = 'AFRICA'), 'Central African Republic', 'ICAO prefix for airport imports.'),
('FK', (SELECT id FROM countries WHERE name = 'Cameroon' AND world_region_code = 'AFRICA'), 'Cameroon', 'ICAO prefix for airport imports.'),
('FN', (SELECT id FROM countries WHERE name = 'Angola' AND world_region_code = 'AFRICA'), 'Angola', 'ICAO prefix for airport imports.'),
('FT', (SELECT id FROM countries WHERE name = 'Chad' AND world_region_code = 'AFRICA'), 'Chad', 'ICAO prefix for airport imports.')
ON DUPLICATE KEY UPDATE
  country_id = VALUES(country_id),
  area_name = VALUES(area_name),
  notes = VALUES(notes),
  is_active = TRUE;
