-- Western Sahara alternative ICAO codes.

USE icaro_ops;

INSERT INTO airport_icao_aliases (
  airport_icao_code,
  alias_icao_code,
  notes
) VALUES
('GSVO', 'GMMH', 'Alternative ICAO code from Western Sahara source table.'),
('GSAI', 'GMML', 'Alternative ICAO code from Western Sahara source table.'),
('GSMA', 'GMMA', 'Alternative ICAO code from Western Sahara source table.')
ON DUPLICATE KEY UPDATE
  notes = VALUES(notes);
