USE icaro_ops;

START TRANSACTION;

UPDATE airports
SET
  latitude = 40.6329,
  longitude = -73.7714,
  elevation_ft = COALESCE(elevation_ft, 13),
  data_quality = 'PARTIAL',
  data_source_name = 'FAA / public airport data - manual coordinate review',
  data_source_url = 'https://weathercams.faa.gov/',
  updated_at_utc = UTC_TIMESTAMP()
WHERE icao_code = 'KJFK';

UPDATE airports
SET
  latitude = 40.7772422,
  longitude = -73.8726056,
  elevation_ft = COALESCE(elevation_ft, 21),
  data_quality = 'PARTIAL',
  data_source_name = 'AirNav / FAA airport data - manual coordinate review',
  data_source_url = 'https://www.airnav.com/airport/KLGA',
  updated_at_utc = UTC_TIMESTAMP()
WHERE icao_code = 'KLGA';

UPDATE airports
SET
  latitude = 40.6924805556,
  longitude = -74.1686877778,
  elevation_ft = COALESCE(elevation_ft, 18),
  data_quality = 'PARTIAL',
  data_source_name = 'Public airport data - manual coordinate review',
  data_source_url = 'https://www.universalweather.com/airports/KEWR-EWR-NEWARK-LIBERTY-INTERNATIONAL-AIRPORT-NEWARK-NEW-JERSEY-UNITED-STATES/',
  updated_at_utc = UTC_TIMESTAMP()
WHERE icao_code = 'KEWR';

COMMIT;
