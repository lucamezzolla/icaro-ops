USE icaro_ops;

UPDATE airports
SET
  latitude = 43.09590,
  longitude = 12.51320
WHERE icao_code = 'LIRZ';

SELECT
  icao_code,
  iata_code,
  name,
  latitude,
  longitude
FROM airports
WHERE icao_code = 'LIRZ';
