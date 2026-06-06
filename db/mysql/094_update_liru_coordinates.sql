USE icaro_ops;

UPDATE airports
SET
  latitude = 41.95210,
  longitude = 12.50220
WHERE icao_code = 'LIRU';

SELECT
  icao_code,
  iata_code,
  name,
  latitude,
  longitude
FROM airports
WHERE icao_code = 'LIRU';
