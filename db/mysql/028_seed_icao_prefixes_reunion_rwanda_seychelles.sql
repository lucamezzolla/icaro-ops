-- ICAO prefix seed for Réunion, Rwanda and Seychelles airport imports.

USE icaro_ops;

INSERT INTO icao_prefixes (
  prefix,
  country_id,
  area_name,
  notes
) VALUES
('FME', (SELECT id FROM countries WHERE name = 'Réunion' AND world_region_code = 'AFRICA'), 'Réunion', 'ICAO prefix for airport imports.'),
('FS', (SELECT id FROM countries WHERE name = 'Seychelles' AND world_region_code = 'AFRICA'), 'Seychelles', 'ICAO prefix for airport imports.'),
('HR', (SELECT id FROM countries WHERE name = 'Rwanda' AND world_region_code = 'AFRICA'), 'Rwanda', 'ICAO prefix for airport imports.')
ON DUPLICATE KEY UPDATE
  country_id = VALUES(country_id),
  area_name = VALUES(area_name),
  notes = VALUES(notes),
  is_active = TRUE;
