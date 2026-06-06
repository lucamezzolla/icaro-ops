USE icaro_ops;

START TRANSACTION;

ALTER TABLE air_routes
  ADD COLUMN IF NOT EXISTS route_category_code VARCHAR(10) NOT NULL DEFAULT 'DOM' AFTER route_code,
  ADD COLUMN IF NOT EXISTS route_public_code VARCHAR(20) NULL AFTER route_category_code;

ALTER TABLE scheduled_services
  ADD COLUMN IF NOT EXISTS flight_route_code VARCHAR(20) NULL AFTER service_code;

UPDATE air_routes ar
LEFT JOIN airports oa ON oa.icao_code = ar.origin_airport_icao_code
LEFT JOIN airports da ON da.icao_code = ar.destination_airport_icao_code
SET ar.route_category_code = CASE
  WHEN ar.route_market = 'HEL' THEN 'HEL'
  WHEN ar.route_market = 'CGO' THEN 'CGO'
  WHEN ar.route_market = 'MIL' THEN 'MIL'
  WHEN ar.route_market = 'RES' THEN 'RES'
  WHEN ar.route_market = 'TRN' THEN 'TRN'
  WHEN ar.route_market = 'CHT' THEN 'CHT'
  WHEN oa.country_id IS NOT NULL AND da.country_id IS NOT NULL AND oa.country_id <> da.country_id THEN 'INT'
  ELSE 'DOM'
END;

UPDATE air_routes
SET route_public_code = CONCAT(route_category_code, '-', LPAD(id, 4, '0'))
WHERE route_public_code IS NULL OR route_public_code = '';

UPDATE scheduled_services ss
JOIN air_routes ar ON ar.id = ss.air_route_id
SET ss.flight_route_code = ar.route_public_code
WHERE ss.flight_route_code IS NULL OR ss.flight_route_code = '';

COMMIT;

SELECT id, route_code, route_category_code, route_public_code
FROM air_routes
ORDER BY id;
