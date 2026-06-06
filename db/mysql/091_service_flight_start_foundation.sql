USE icaro_ops;

START TRANSACTION;

ALTER TABLE scheduled_flight_instances
  MODIFY COLUMN route_id BIGINT UNSIGNED NULL;

ALTER TABLE scheduled_flight_instances
  ADD COLUMN IF NOT EXISTS air_route_id BIGINT UNSIGNED NULL AFTER route_id,
  ADD COLUMN IF NOT EXISTS scheduled_service_id BIGINT UNSIGNED NULL AFTER air_route_id,
  ADD COLUMN IF NOT EXISTS flight_operation_type VARCHAR(30) NOT NULL DEFAULT 'SCHEDULED' AFTER flight_code,
  ADD COLUMN IF NOT EXISTS required_aircraft_class VARCHAR(40) NOT NULL DEFAULT 'LIGHT_COMMERCIAL' AFTER destination_airport_icao_code,
  ADD COLUMN IF NOT EXISTS preferred_aircraft_model_id BIGINT UNSIGNED NULL AFTER required_aircraft_class,
  ADD COLUMN IF NOT EXISTS planned_aircraft_id BIGINT UNSIGNED NULL AFTER preferred_aircraft_model_id,
  ADD COLUMN IF NOT EXISTS dispatch_aircraft_id BIGINT UNSIGNED NULL AFTER planned_aircraft_id,
  ADD COLUMN IF NOT EXISTS dispatch_status VARCHAR(30) NOT NULL DEFAULT 'ASSIGNED' AFTER status,
  ADD COLUMN IF NOT EXISTS backup_used TINYINT(1) NOT NULL DEFAULT 0 AFTER dispatch_status,
  ADD COLUMN IF NOT EXISTS backup_reason VARCHAR(500) NULL AFTER backup_used,
  ADD COLUMN IF NOT EXISTS schedule_conflict_status VARCHAR(30) NOT NULL DEFAULT 'NONE' AFTER backup_reason;

COMMIT;

SELECT 'Service flight start foundation installed' AS result;
