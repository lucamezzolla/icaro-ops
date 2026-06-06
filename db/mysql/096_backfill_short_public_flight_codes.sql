USE icaro_ops;

START TRANSACTION;

ALTER TABLE scheduled_services
  ADD COLUMN IF NOT EXISTS flight_route_code VARCHAR(20) NULL AFTER service_code;

-- Backfill public short flight codes from long internal service_code values.
-- Example:
-- DOM-0009-C002-OND-ONDEMAND-1780767477 -> DOM-0009
UPDATE scheduled_services
SET flight_route_code = CONCAT(
  SUBSTRING_INDEX(service_code, '-', 1),
  '-',
  SUBSTRING_INDEX(SUBSTRING_INDEX(service_code, '-', 2), '-', -1)
)
WHERE (
    flight_route_code IS NULL
    OR flight_route_code = ''
    OR flight_route_code LIKE '%-%-%'
  )
  AND service_code REGEXP '^[A-Z]{3}-[0-9]{4}-';

-- Fallback for older rows still linked to hidden air_routes.
UPDATE scheduled_services ss
JOIN air_routes ar
  ON ar.id = ss.air_route_id
SET ss.flight_route_code = ar.route_public_code
WHERE (ss.flight_route_code IS NULL OR ss.flight_route_code = '')
  AND ar.route_public_code IS NOT NULL
  AND ar.route_public_code <> '';

COMMIT;

SELECT
  id,
  flight_route_code AS public_flight_code,
  service_code AS internal_code
FROM scheduled_services
ORDER BY id DESC
LIMIT 20;
