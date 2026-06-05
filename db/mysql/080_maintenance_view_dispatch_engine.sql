-- Icaro Ops maintenance view and dispatch engine foundation.
--
-- Purpose:
--   - manage each owned aircraft maintenance from its own page
--   - allow maintenance scheduling/completion while aircraft is on ground
--   - add route dispatch outcome tracking
--   - introduce backup aircraft dispatch logic foundation
--
-- Run:
--   sudo mysql icaro_ops < db/mysql/080_maintenance_view_dispatch_engine.sql

USE icaro_ops;

START TRANSACTION;

ALTER TABLE company_routes
  ADD COLUMN IF NOT EXISTS auto_dispatch_enabled BOOLEAN NOT NULL DEFAULT TRUE AFTER recurrence_type,
  ADD COLUMN IF NOT EXISTS allow_backup_aircraft BOOLEAN NOT NULL DEFAULT TRUE AFTER auto_dispatch_enabled,
  ADD COLUMN IF NOT EXISTS missed_dispatch_count INT UNSIGNED NOT NULL DEFAULT 0 AFTER status,
  ADD COLUMN IF NOT EXISTS last_dispatch_attempt_at_utc DATETIME NULL AFTER missed_dispatch_count,
  ADD COLUMN IF NOT EXISTS last_dispatch_result VARCHAR(40) NULL AFTER last_dispatch_attempt_at_utc;

CREATE TABLE IF NOT EXISTS route_dispatch_attempts (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,

  route_id BIGINT UNSIGNED NOT NULL,
  company_id BIGINT UNSIGNED NOT NULL,

  scheduled_departure_at_utc DATETIME NOT NULL,
  attempted_at_utc TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

  result VARCHAR(40) NOT NULL,
  reason VARCHAR(500) NULL,

  selected_aircraft_id BIGINT UNSIGNED NULL,
  selected_aircraft_role VARCHAR(30) NULL,

  reputation_delta INT NOT NULL DEFAULT 0,
  budget_delta DECIMAL(15,2) NOT NULL DEFAULT 0.00,
  currency_code CHAR(3) NOT NULL DEFAULT 'EUR',

  mailbox_message_id BIGINT UNSIGNED NULL,

  PRIMARY KEY (id),
  KEY idx_dispatch_attempts_route_time (route_id, scheduled_departure_at_utc),
  KEY idx_dispatch_attempts_company_time (company_id, attempted_at_utc),

  CONSTRAINT fk_dispatch_attempts_route
    FOREIGN KEY (route_id)
    REFERENCES company_routes(id)
    ON UPDATE CASCADE
    ON DELETE CASCADE,

  CONSTRAINT fk_dispatch_attempts_company
    FOREIGN KEY (company_id)
    REFERENCES companies(id)
    ON UPDATE CASCADE
    ON DELETE CASCADE,

  CONSTRAINT fk_dispatch_attempts_aircraft
    FOREIGN KEY (selected_aircraft_id)
    REFERENCES company_aircraft(id)
    ON UPDATE CASCADE
    ON DELETE SET NULL,

  CONSTRAINT fk_dispatch_attempts_mailbox
    FOREIGN KEY (mailbox_message_id)
    REFERENCES game_mailbox_messages(id)
    ON UPDATE CASCADE
    ON DELETE SET NULL,

  CONSTRAINT chk_dispatch_attempts_result
    CHECK (result IN (
      'STARTED_PRIMARY',
      'STARTED_BACKUP',
      'DELAYED_NO_AIRCRAFT',
      'CANCELLED_NO_AIRCRAFT',
      'BLOCKED_MAINTENANCE',
      'BLOCKED_CREW',
      'SKIPPED_ALREADY_PROCESSED'
    )),

  CONSTRAINT chk_dispatch_attempts_aircraft_role
    CHECK (selected_aircraft_role IS NULL OR selected_aircraft_role IN ('PRIMARY', 'BACKUP'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE OR REPLACE VIEW v_company_routes AS
SELECT
  r.id AS route_id,
  r.company_id,
  co.company_name,

  r.aircraft_id,
  ca.registration_code,
  am.manufacturer,
  am.model_name,
  am.model_code,
  am.icao_type_code,
  am.passenger_capacity_standard,
  am.cruise_speed_kmh,
  am.range_km,
  am.fuel_burn_kg_per_hour,
  am.maintenance_cost_per_hour,

  r.origin_airport_icao_code,
  oa.name AS origin_airport_name,
  oa.latitude AS origin_latitude,
  oa.longitude AS origin_longitude,

  r.destination_airport_icao_code,
  da.name AS destination_airport_name,
  da.latitude AS destination_latitude,
  da.longitude AS destination_longitude,

  r.scheduled_departure_time_utc,
  r.recurrence_type,
  r.auto_dispatch_enabled,
  r.allow_backup_aircraft,
  r.planned_distance_km,
  r.planned_duration_minutes,
  r.ticket_price,
  r.currency_code,
  r.status,
  r.missed_dispatch_count,
  r.last_dispatch_attempt_at_utc,
  r.last_dispatch_result,

  r.assigned_pilot_1_id,
  r.assigned_pilot_2_id,
  r.assigned_technician_id,

  p1.display_name AS pilot_1_name,
  p2.display_name AS pilot_2_name,
  tech.display_name AS technician_name,

  CASE
    WHEN r.aircraft_id IS NULL THEN 'UNASSIGNED_AIRCRAFT'
    WHEN ca.status NOT IN ('AVAILABLE', 'PARKED') THEN 'AIRCRAFT_NOT_READY'
    WHEN ca.current_airport_icao_code <> r.origin_airport_icao_code THEN 'AIRCRAFT_NOT_AT_ORIGIN'
    WHEN r.assigned_pilot_1_id IS NULL OR r.assigned_pilot_2_id IS NULL THEN 'PILOTS_NOT_ASSIGNED'
    ELSE 'READY'
  END AS dispatch_readiness

FROM company_routes r
JOIN companies co
  ON co.id = r.company_id
LEFT JOIN company_aircraft ca
  ON ca.id = r.aircraft_id
LEFT JOIN aircraft_models am
  ON am.id = ca.aircraft_model_id
JOIN airports oa
  ON oa.icao_code = r.origin_airport_icao_code
JOIN airports da
  ON da.icao_code = r.destination_airport_icao_code
LEFT JOIN company_staff p1
  ON p1.id = r.assigned_pilot_1_id
LEFT JOIN company_staff p2
  ON p2.id = r.assigned_pilot_2_id
LEFT JOIN company_staff tech
  ON tech.id = r.assigned_technician_id;

CREATE OR REPLACE VIEW v_company_aircraft_maintenance_detail AS
SELECT
  ca.id AS aircraft_id,
  ca.company_id,
  co.company_name,

  ca.registration_code,
  ca.serial_number,
  ca.manufacture_year,
  ca.ownership_status,
  ca.acquisition_type,
  ca.purchase_price,
  ca.current_market_value,
  ca.currency_code,
  ca.home_base_icao_code,
  hb.name AS home_base_name,
  ca.current_airport_icao_code,
  cb.name AS current_airport_name,
  ca.condition_percent,
  ca.airframe_hours,
  ca.cycles_count,
  ca.status AS aircraft_status,

  am.id AS aircraft_model_id,
  am.manufacturer,
  am.model_name,
  am.model_code,
  am.icao_type_code,
  am.operation_role,
  am.passenger_capacity_standard,
  am.range_km,
  am.cruise_speed_kmh,
  am.image_asset_path,

  mp.routine_maintenance_interval_hours,
  mp.routine_maintenance_interval_cycles,
  mp.condition_loss_per_flight_percent,
  mp.condition_warning_threshold_percent,
  mp.condition_grounding_threshold_percent,
  mp.routine_maintenance_duration_hours,
  mp.minor_repair_duration_hours,
  mp.major_repair_duration_hours,
  mp.technician_license_required,

  CASE
    WHEN ca.status = 'IN_FLIGHT' THEN 'IN_FLIGHT'
    WHEN ca.status = 'MAINTENANCE' THEN 'MAINTENANCE_IN_PROGRESS'
    WHEN ca.condition_percent <= mp.condition_grounding_threshold_percent THEN 'GROUNDED_REQUIRED'
    WHEN ca.condition_percent <= mp.condition_warning_threshold_percent THEN 'MAINTENANCE_WARNING'
    WHEN ca.airframe_hours >= mp.routine_maintenance_interval_hours THEN 'ROUTINE_HOURS_DUE'
    WHEN ca.cycles_count >= mp.routine_maintenance_interval_cycles THEN 'ROUTINE_CYCLES_DUE'
    ELSE 'OK'
  END AS maintenance_state,

  (
    SELECT COUNT(*)
    FROM aircraft_operational_events e
    WHERE e.aircraft_id = ca.id
      AND e.status IN ('OPEN', 'IN_PROGRESS')
  ) AS open_event_count

FROM company_aircraft ca
JOIN companies co
  ON co.id = ca.company_id
JOIN airports hb
  ON hb.icao_code = ca.home_base_icao_code
JOIN airports cb
  ON cb.icao_code = ca.current_airport_icao_code
JOIN aircraft_models am
  ON am.id = ca.aircraft_model_id
LEFT JOIN aircraft_maintenance_profiles mp
  ON mp.aircraft_model_id = am.id;

COMMIT;
