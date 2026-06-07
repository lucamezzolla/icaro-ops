-- Icaro Ops - Update LPPT airport coordinates.
--
-- Purpose:
--   Ensure Lisbon / Humberto Delgado Airport (LPPT / LIS) has usable coordinates
--   for maps, delivery airport validation, routes and flight positioning.
--
-- Run:
--   sudo mysql icaro_ops < db/mysql/116_update_lppt_coordinates.sql

USE icaro_ops;

START TRANSACTION;

INSERT INTO airports (
  icao_code,
  country_id,
  icao_prefix,
  iata_code,
  name,
  city,
  location_name,
  subdivision_name,
  latitude,
  longitude,
  elevation_ft,
  airport_type,
  service_category,
  is_civilian,
  is_commercial,
  is_military,
  is_closed,
  operator_country_name,
  aip_url,
  chart_url,
  source_rating_percent,
  data_source_name,
  data_source_url,
  data_quality
)
SELECT
  'LPPT',
  c.id,
  'LP',
  'LIS',
  'Lisbon Humberto Delgado Airport',
  'Lisbon',
  'Lisbon',
  'Lisbon',
  38.7813000,
  -9.1359200,
  374,
  'AIRPORT',
  'INTERNATIONAL',
  TRUE,
  TRUE,
  FALSE,
  FALSE,
  NULL,
  NULL,
  NULL,
  90,
  'Manual correction',
  'https://www.ana.pt/en/lis/home',
  'VERIFIED'
FROM countries c
WHERE c.name = 'Portugal'
  AND c.world_region_code = 'EUROPE'
LIMIT 1
ON DUPLICATE KEY UPDATE
  country_id = VALUES(country_id),
  icao_prefix = VALUES(icao_prefix),
  iata_code = VALUES(iata_code),
  name = VALUES(name),
  city = VALUES(city),
  location_name = VALUES(location_name),
  subdivision_name = VALUES(subdivision_name),
  latitude = VALUES(latitude),
  longitude = VALUES(longitude),
  elevation_ft = VALUES(elevation_ft),
  airport_type = VALUES(airport_type),
  service_category = VALUES(service_category),
  is_civilian = VALUES(is_civilian),
  is_commercial = VALUES(is_commercial),
  is_military = VALUES(is_military),
  is_closed = VALUES(is_closed),
  operator_country_name = VALUES(operator_country_name),
  aip_url = VALUES(aip_url),
  chart_url = VALUES(chart_url),
  source_rating_percent = VALUES(source_rating_percent),
  data_source_name = VALUES(data_source_name),
  data_source_url = VALUES(data_source_url),
  data_quality = VALUES(data_quality);

COMMIT;
