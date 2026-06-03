-- ICAO prefix seed for West Africa batch.

USE icaro_ops;

INSERT INTO icao_prefixes (
  prefix,
  country_id,
  area_name,
  notes
) VALUES
('DB', 43, 'Benin', 'ICAO prefix for airport imports.'),
('DF', 44, 'Burkina Faso', 'ICAO prefix for airport imports.'),
('DG', 48, 'Ghana', 'ICAO prefix for airport imports.'),
('DI', 46, 'Ivory Coast', 'ICAO prefix for airport imports.'),
('GB', 47, 'The Gambia', 'ICAO prefix for airport imports.'),
('GV', 45, 'Cape Verde', 'ICAO prefix for airport imports.')
ON DUPLICATE KEY UPDATE
  country_id = VALUES(country_id),
  area_name = VALUES(area_name),
  notes = VALUES(notes),
  is_active = TRUE;
