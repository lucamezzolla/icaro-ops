-- ICAO prefix seed for Central Africa west/coast airport imports.

USE icaro_ops;

INSERT INTO icao_prefixes (
  prefix,
  country_id,
  area_name,
  notes
) VALUES
('FC', (SELECT id FROM countries WHERE name = 'Republic of the Congo' AND world_region_code = 'AFRICA'), 'Republic of the Congo', 'ICAO prefix for airport imports.'),
('FG', (SELECT id FROM countries WHERE name = 'Equatorial Guinea' AND world_region_code = 'AFRICA'), 'Equatorial Guinea', 'ICAO prefix for airport imports.'),
('FO', (SELECT id FROM countries WHERE name = 'Gabon' AND world_region_code = 'AFRICA'), 'Gabon', 'ICAO prefix for airport imports.'),
('FP', (SELECT id FROM countries WHERE name = 'São Tomé and Príncipe' AND world_region_code = 'AFRICA'), 'São Tomé and Príncipe', 'ICAO prefix for airport imports.'),
('FZ', (SELECT id FROM countries WHERE name = 'Democratic Republic of the Congo' AND world_region_code = 'AFRICA'), 'Democratic Republic of the Congo', 'ICAO prefix for airport imports.')
ON DUPLICATE KEY UPDATE
  country_id = VALUES(country_id),
  area_name = VALUES(area_name),
  notes = VALUES(notes),
  is_active = TRUE;
