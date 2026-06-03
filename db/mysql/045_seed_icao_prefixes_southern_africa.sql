-- ICAO prefix seed for Botswana, Eswatini, Lesotho, Namibia and South Africa.

USE icaro_ops;

INSERT INTO icao_prefixes (
  prefix,
  country_id,
  area_name,
  notes
) VALUES
('FA', (SELECT id FROM countries WHERE name = 'South Africa' AND world_region_code = 'AFRICA'), 'South Africa', 'ICAO prefix for airport imports.'),
('FB', (SELECT id FROM countries WHERE name = 'Botswana' AND world_region_code = 'AFRICA'), 'Botswana', 'ICAO prefix for airport imports.'),
('FD', (SELECT id FROM countries WHERE name = 'Eswatini' AND world_region_code = 'AFRICA'), 'Eswatini', 'ICAO prefix for airport imports.'),
('FX', (SELECT id FROM countries WHERE name = 'Lesotho' AND world_region_code = 'AFRICA'), 'Lesotho', 'ICAO prefix for airport imports.'),
('FY', (SELECT id FROM countries WHERE name = 'Namibia' AND world_region_code = 'AFRICA'), 'Namibia', 'ICAO prefix for airport imports.')
ON DUPLICATE KEY UPDATE
  country_id = VALUES(country_id),
  area_name = VALUES(area_name),
  notes = VALUES(notes),
  is_active = TRUE;
