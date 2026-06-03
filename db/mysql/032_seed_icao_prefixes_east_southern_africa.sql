-- ICAO prefix seed for Somalia, South Sudan, Tanzania, Uganda, Zambia and Zimbabwe.

USE icaro_ops;

INSERT INTO icao_prefixes (
  prefix,
  country_id,
  area_name,
  notes
) VALUES
('FL', (SELECT id FROM countries WHERE name = 'Zambia' AND world_region_code = 'AFRICA'), 'Zambia', 'ICAO prefix for airport imports.'),
('FV', (SELECT id FROM countries WHERE name = 'Zimbabwe' AND world_region_code = 'AFRICA'), 'Zimbabwe', 'ICAO prefix for airport imports.'),
('HC', (SELECT id FROM countries WHERE name = 'Somalia' AND world_region_code = 'AFRICA'), 'Somalia', 'ICAO prefix for airport imports.'),
('HJ', (SELECT id FROM countries WHERE name = 'South Sudan' AND world_region_code = 'AFRICA'), 'South Sudan', 'ICAO prefix for airport imports.'),
('HS', (SELECT id FROM countries WHERE name = 'South Sudan' AND world_region_code = 'AFRICA'), 'South Sudan', 'ICAO prefix for airport imports.'),
('HT', (SELECT id FROM countries WHERE name = 'Tanzania' AND world_region_code = 'AFRICA'), 'Tanzania', 'ICAO prefix for airport imports.'),
('HU', (SELECT id FROM countries WHERE name = 'Uganda' AND world_region_code = 'AFRICA'), 'Uganda', 'ICAO prefix for airport imports.')
ON DUPLICATE KEY UPDATE
  country_id = VALUES(country_id),
  area_name = VALUES(area_name),
  notes = VALUES(notes),
  is_active = TRUE;
