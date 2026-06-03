-- ICAO prefix seed for North Africa airport imports.

USE icaro_ops;

INSERT INTO icao_prefixes (
  prefix,
  country_id,
  area_name,
  notes
) VALUES
('HE', (SELECT id FROM countries WHERE name = 'Egypt' AND world_region_code = 'AFRICA'), 'Egypt', 'ICAO prefix for airport imports.'),
('HL', (SELECT id FROM countries WHERE name = 'Libya' AND world_region_code = 'AFRICA'), 'Libya', 'ICAO prefix for airport imports.'),
('GM', (SELECT id FROM countries WHERE name = 'Morocco' AND world_region_code = 'AFRICA'), 'Morocco', 'ICAO prefix for airport imports.'),
('HS', (SELECT id FROM countries WHERE name = 'Sudan' AND world_region_code = 'AFRICA'), 'Sudan', 'ICAO prefix for airport imports.'),
('DT', (SELECT id FROM countries WHERE name = 'Tunisia' AND world_region_code = 'AFRICA'), 'Tunisia', 'ICAO prefix for airport imports.'),
('GS', (SELECT id FROM countries WHERE name = 'Western Sahara' AND world_region_code = 'AFRICA'), 'Western Sahara', 'ICAO prefix for airport imports.')
ON DUPLICATE KEY UPDATE
  country_id = VALUES(country_id),
  area_name = VALUES(area_name),
  notes = VALUES(notes),
  is_active = TRUE;
