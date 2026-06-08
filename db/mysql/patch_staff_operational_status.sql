ALTER TABLE scheduled_flight_instances
  ADD COLUMN IF NOT EXISTS pilot_1_staff_id BIGINT(20) UNSIGNED NULL AFTER dispatch_aircraft_id,
  ADD COLUMN IF NOT EXISTS pilot_2_staff_id BIGINT(20) UNSIGNED NULL AFTER pilot_1_staff_id,
  ADD COLUMN IF NOT EXISTS technician_staff_id BIGINT(20) UNSIGNED NULL AFTER pilot_2_staff_id;

CREATE INDEX IF NOT EXISTS idx_sfi_pilot_1_staff_status
  ON scheduled_flight_instances (pilot_1_staff_id, status);

CREATE INDEX IF NOT EXISTS idx_sfi_pilot_2_staff_status
  ON scheduled_flight_instances (pilot_2_staff_id, status);

CREATE INDEX IF NOT EXISTS idx_sfi_technician_staff_status
  ON scheduled_flight_instances (technician_staff_id, status);
