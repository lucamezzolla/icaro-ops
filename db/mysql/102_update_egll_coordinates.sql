USE icaro_ops;

UPDATE airports
SET
  latitude = 51.47000,
  longitude = -0.45430
WHERE icao_code = 'EGLL';

SELECT
  icao_code,
  iata_code,
  name,
  latitude,
  longitude
FROM airports
WHERE icao_code = 'EGLL';
