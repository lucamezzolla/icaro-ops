-- ICAO prefix seed for East Africa / Indian Ocean airport imports.
-- Some ICAO allocations such as FM are shared, so specific prefixes are used where needed.

USE icaro_ops;

INSERT INTO icao_prefixes (
  prefix,
  country_id,
  area_name,
  notes
) VALUES
('FI', (SELECT id FROM countries WHERE name = 'Mauritius' AND world_region_code = 'AFRICA'), 'Mauritius', 'ICAO prefix for airport imports.'),
('FMCZ', (SELECT id FROM countries WHERE name = 'Mayotte' AND world_region_code = 'AFRICA'), 'Mayotte', 'ICAO prefix for airport imports.'),
('FMM', (SELECT id FROM countries WHERE name = 'Madagascar' AND world_region_code = 'AFRICA'), 'Madagascar', 'ICAO prefix for airport imports.'),
('FMN', (SELECT id FROM countries WHERE name = 'Madagascar' AND world_region_code = 'AFRICA'), 'Madagascar', 'ICAO prefix for airport imports.'),
('FMS', (SELECT id FROM countries WHERE name = 'Madagascar' AND world_region_code = 'AFRICA'), 'Madagascar', 'ICAO prefix for airport imports.'),
('FQ', (SELECT id FROM countries WHERE name = 'Mozambique' AND world_region_code = 'AFRICA'), 'Mozambique', 'ICAO prefix for airport imports.'),
('FW', (SELECT id FROM countries WHERE name = 'Malawi' AND world_region_code = 'AFRICA'), 'Malawi', 'ICAO prefix for airport imports.'),
('HA', (SELECT id FROM countries WHERE name = 'Ethiopia' AND world_region_code = 'AFRICA'), 'Ethiopia', 'ICAO prefix for airport imports.'),
('HK', (SELECT id FROM countries WHERE name = 'Kenya' AND world_region_code = 'AFRICA'), 'Kenya', 'ICAO prefix for airport imports.')
ON DUPLICATE KEY UPDATE
  country_id = VALUES(country_id),
  area_name = VALUES(area_name),
  notes = VALUES(notes),
  is_active = TRUE;
