USE icaro_ops;

UPDATE airports
SET
  latitude = 45.50530,
  longitude = 12.35190
WHERE icao_code = 'LIPZ';

SELECT
  icao_code,
  iata_code,
  name,
  latitude,
  longitude
FROM airports
WHERE icao_code = 'LIPZ';
