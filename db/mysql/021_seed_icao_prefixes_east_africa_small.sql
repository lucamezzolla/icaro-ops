-- ICAO prefix seed for this East Africa / Indian Ocean import batch.

USE icaro_ops;

INSERT INTO icao_prefixes (
  prefix,
  country_id,
  area_name,
  notes
) VALUES
('HB', (SELECT id FROM countries WHERE name = 'Burundi' AND world_region_code = 'AFRICA'), 'Burundi', 'ICAO prefix for airport imports.'),
('HD', (SELECT id FROM countries WHERE name = 'Djibouti' AND world_region_code = 'AFRICA'), 'Djibouti', 'ICAO prefix for airport imports.'),
('HH', (SELECT id FROM countries WHERE name = 'Eritrea' AND world_region_code = 'AFRICA'), 'Eritrea', 'ICAO prefix for airport imports.'),
('FJ', (SELECT id FROM countries WHERE name = 'British Indian Ocean Territory' AND world_region_code = 'AFRICA'), 'British Indian Ocean Territory', 'ICAO prefix for airport imports.'),
('FM', (SELECT id FROM countries WHERE name = 'Comoros' AND world_region_code = 'AFRICA'), 'Comoros', 'ICAO prefix for airport imports.')
ON DUPLICATE KEY UPDATE
  country_id = VALUES(country_id),
  area_name = VALUES(area_name),
  notes = VALUES(notes),
  is_active = TRUE;
