USE icaro_ops;

UPDATE airports
SET
  latitude = 41.29710,
  longitude = 2.07850
WHERE icao_code = 'LEBL';

SELECT
  icao_code,
  iata_code,
  name,
  latitude,
  longitude
FROM airports
WHERE icao_code = 'LEBL';
