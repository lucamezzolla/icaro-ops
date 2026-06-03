-- Burundi runway source notes.
-- The Burundi source includes runway text. Store raw notes separately for later normalization.

USE icaro_ops;

INSERT INTO airport_runway_source_notes (
  airport_icao_code,
  source_note,
  data_source_name
) VALUES
('HBBA', '17/35: 11,990 x 187, Asphalt', 'Wikipedia - List of airports in Burundi'),
('HBBE', '12/30: 3,270 x 66, Grass; H1: 82 dia., Grass; H2: 82 dia., Grass', 'Wikipedia - List of airports in Burundi'),
('HBBL', 'Closed', 'Wikipedia - List of airports in Burundi'),
('HBBO', '12/30: 3,480 x 75, Grass', 'Wikipedia - List of airports in Burundi')
ON DUPLICATE KEY UPDATE
  source_note = VALUES(source_note),
  data_source_name = VALUES(data_source_name);
