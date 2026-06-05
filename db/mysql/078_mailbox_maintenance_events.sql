-- Icaro Ops mailbox, maintenance and aircraft event foundation.
--
-- Purpose:
--   Add in-game mailbox and persistent operational events for:
--   - maintenance required
--   - aircraft faults
--   - in-flight incidents
--   - dispatch blocked
--
-- Run:
--   sudo mysql icaro_ops < db/mysql/078_mailbox_maintenance_events.sql

USE icaro_ops;

START TRANSACTION;

CREATE TABLE IF NOT EXISTS game_mailbox_messages (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,

  company_id BIGINT UNSIGNED NOT NULL,

  message_type VARCHAR(40) NOT NULL,
  severity VARCHAR(20) NOT NULL DEFAULT 'INFO',
  status VARCHAR(30) NOT NULL DEFAULT 'UNREAD',

  title VARCHAR(180) NOT NULL,
  body TEXT NOT NULL,

  related_entity_type VARCHAR(50) NULL,
  related_entity_id BIGINT UNSIGNED NULL,

  action_payload_json JSON NULL,

  created_at_utc TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  read_at_utc TIMESTAMP NULL,
  resolved_at_utc TIMESTAMP NULL,

  PRIMARY KEY (id),
  KEY idx_mailbox_company_status (company_id, status, created_at_utc),
  KEY idx_mailbox_related (related_entity_type, related_entity_id),

  CONSTRAINT fk_mailbox_company
    FOREIGN KEY (company_id)
    REFERENCES companies(id)
    ON UPDATE CASCADE
    ON DELETE CASCADE,

  CONSTRAINT chk_mailbox_severity
    CHECK (severity IN ('INFO', 'WARNING', 'CRITICAL')),

  CONSTRAINT chk_mailbox_status
    CHECK (status IN ('UNREAD', 'READ', 'RESOLVED', 'ARCHIVED')),

  CONSTRAINT chk_mailbox_type
    CHECK (message_type IN (
      'SYSTEM',
      'DISPATCH_BLOCKED',
      'MAINTENANCE_REQUIRED',
      'AIRCRAFT_FAULT_GROUND',
      'AIRCRAFT_FAULT_IN_FLIGHT',
      'FLIGHT_COMPLETED',
      'FINANCE',
      'STAFF'
    ))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS aircraft_maintenance_profiles (
  aircraft_model_id BIGINT UNSIGNED NOT NULL,

  routine_maintenance_interval_hours INT UNSIGNED NOT NULL DEFAULT 100,
  routine_maintenance_interval_cycles INT UNSIGNED NOT NULL DEFAULT 80,

  condition_loss_per_flight_percent DECIMAL(5,2) NOT NULL DEFAULT 0.35,
  condition_warning_threshold_percent DECIMAL(5,2) NOT NULL DEFAULT 70.00,
  condition_grounding_threshold_percent DECIMAL(5,2) NOT NULL DEFAULT 45.00,

  minor_fault_probability_percent DECIMAL(5,2) NOT NULL DEFAULT 1.00,
  major_fault_probability_percent DECIMAL(5,2) NOT NULL DEFAULT 0.20,
  in_flight_fault_probability_percent DECIMAL(5,2) NOT NULL DEFAULT 0.05,

  routine_maintenance_duration_hours INT UNSIGNED NOT NULL DEFAULT 8,
  minor_repair_duration_hours INT UNSIGNED NOT NULL DEFAULT 12,
  major_repair_duration_hours INT UNSIGNED NOT NULL DEFAULT 24,

  technician_license_required VARCHAR(50) NULL,

  updated_at_utc TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

  PRIMARY KEY (aircraft_model_id),

  CONSTRAINT fk_maintenance_profiles_model
    FOREIGN KEY (aircraft_model_id)
    REFERENCES aircraft_models(id)
    ON UPDATE CASCADE
    ON DELETE CASCADE,

  CONSTRAINT fk_maintenance_profiles_license
    FOREIGN KEY (technician_license_required)
    REFERENCES staff_license_types(code)
    ON UPDATE CASCADE
    ON DELETE SET NULL,

  CONSTRAINT chk_maintenance_profiles_percentages
    CHECK (
      condition_loss_per_flight_percent >= 0
      AND condition_warning_threshold_percent BETWEEN 0 AND 100
      AND condition_grounding_threshold_percent BETWEEN 0 AND 100
      AND minor_fault_probability_percent BETWEEN 0 AND 100
      AND major_fault_probability_percent BETWEEN 0 AND 100
      AND in_flight_fault_probability_percent BETWEEN 0 AND 100
    )
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS aircraft_operational_events (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,

  company_id BIGINT UNSIGNED NOT NULL,
  aircraft_id BIGINT UNSIGNED NOT NULL,

  flight_instance_id BIGINT UNSIGNED NULL,

  event_type VARCHAR(40) NOT NULL,
  severity VARCHAR(20) NOT NULL,
  status VARCHAR(30) NOT NULL DEFAULT 'OPEN',

  title VARCHAR(180) NOT NULL,
  description TEXT NOT NULL,

  condition_percent_before DECIMAL(5,2) NULL,
  condition_percent_after DECIMAL(5,2) NULL,

  required_technician_license VARCHAR(50) NULL,

  started_at_utc TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  estimated_completed_at_utc DATETIME NULL,
  completed_at_utc DATETIME NULL,

  mailbox_message_id BIGINT UNSIGNED NULL,

  PRIMARY KEY (id),
  KEY idx_aircraft_events_company_status (company_id, status, started_at_utc),
  KEY idx_aircraft_events_aircraft (aircraft_id, status),
  KEY idx_aircraft_events_flight (flight_instance_id),

  CONSTRAINT fk_aircraft_events_company
    FOREIGN KEY (company_id)
    REFERENCES companies(id)
    ON UPDATE CASCADE
    ON DELETE CASCADE,

  CONSTRAINT fk_aircraft_events_aircraft
    FOREIGN KEY (aircraft_id)
    REFERENCES company_aircraft(id)
    ON UPDATE CASCADE
    ON DELETE CASCADE,

  CONSTRAINT fk_aircraft_events_flight
    FOREIGN KEY (flight_instance_id)
    REFERENCES scheduled_flight_instances(id)
    ON UPDATE CASCADE
    ON DELETE SET NULL,

  CONSTRAINT fk_aircraft_events_license
    FOREIGN KEY (required_technician_license)
    REFERENCES staff_license_types(code)
    ON UPDATE CASCADE
    ON DELETE SET NULL,

  CONSTRAINT fk_aircraft_events_mailbox
    FOREIGN KEY (mailbox_message_id)
    REFERENCES game_mailbox_messages(id)
    ON UPDATE CASCADE
    ON DELETE SET NULL,

  CONSTRAINT chk_aircraft_events_type
    CHECK (event_type IN (
      'ROUTINE_MAINTENANCE_DUE',
      'CONDITION_WARNING',
      'GROUND_FAULT_MINOR',
      'GROUND_FAULT_MAJOR',
      'IN_FLIGHT_FAULT_MINOR',
      'IN_FLIGHT_FAULT_MAJOR',
      'DISPATCH_BLOCKED'
    )),

  CONSTRAINT chk_aircraft_events_severity
    CHECK (severity IN ('INFO', 'WARNING', 'CRITICAL')),

  CONSTRAINT chk_aircraft_events_status
    CHECK (status IN ('OPEN', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO aircraft_maintenance_profiles (
  aircraft_model_id,
  routine_maintenance_interval_hours,
  routine_maintenance_interval_cycles,
  condition_loss_per_flight_percent,
  condition_warning_threshold_percent,
  condition_grounding_threshold_percent,
  minor_fault_probability_percent,
  major_fault_probability_percent,
  in_flight_fault_probability_percent,
  routine_maintenance_duration_hours,
  minor_repair_duration_hours,
  major_repair_duration_hours,
  technician_license_required
)
SELECT
  am.id,
  CASE am.model_code
    WHEN 'C208B_GRAND_CARAVAN_EX' THEN 100
    WHEN 'PC12_NGX' THEN 120
    WHEN 'B350_KING_AIR_360' THEN 120
    WHEN 'DHC6_TWIN_OTTER_400' THEN 90
    WHEN 'L410_NG' THEN 100
    WHEN 'SAAB_340B' THEN 130
    WHEN 'ATR42_600' THEN 150
    WHEN 'EMB120ER_BRASILIA' THEN 120
    ELSE 100
  END,
  CASE am.model_code
    WHEN 'C208B_GRAND_CARAVAN_EX' THEN 80
    WHEN 'DHC6_TWIN_OTTER_400' THEN 70
    ELSE 90
  END,
  CASE am.model_code
    WHEN 'C208B_GRAND_CARAVAN_EX' THEN 0.45
    WHEN 'DHC6_TWIN_OTTER_400' THEN 0.55
    WHEN 'ATR42_600' THEN 0.35
    ELSE 0.40
  END,
  70.00,
  45.00,
  CASE am.model_code
    WHEN 'C208B_GRAND_CARAVAN_EX' THEN 1.20
    WHEN 'DHC6_TWIN_OTTER_400' THEN 1.60
    WHEN 'CONCORDE' THEN 3.50
    ELSE 1.00
  END,
  CASE am.model_code
    WHEN 'C208B_GRAND_CARAVAN_EX' THEN 0.25
    WHEN 'DHC6_TWIN_OTTER_400' THEN 0.35
    WHEN 'CONCORDE' THEN 1.50
    ELSE 0.20
  END,
  CASE am.model_code
    WHEN 'C208B_GRAND_CARAVAN_EX' THEN 0.05
    WHEN 'DHC6_TWIN_OTTER_400' THEN 0.08
    WHEN 'CONCORDE' THEN 0.40
    ELSE 0.05
  END,
  8,
  12,
  24,
  CASE am.model_code
    WHEN 'C208B_GRAND_CARAVAN_EX' THEN 'C208_MAINT'
    ELSE 'TURBOPROP_MAINT'
  END
FROM aircraft_models am
WHERE am.model_code IN (
  'C208B_GRAND_CARAVAN_EX',
  'PC12_NGX',
  'B350_KING_AIR_360',
  'DHC6_TWIN_OTTER_400',
  'L410_NG',
  'SAAB_340B',
  'ATR42_600',
  'EMB120ER_BRASILIA',
  'CONCORDE'
)
ON DUPLICATE KEY UPDATE
  routine_maintenance_interval_hours = VALUES(routine_maintenance_interval_hours),
  routine_maintenance_interval_cycles = VALUES(routine_maintenance_interval_cycles),
  condition_loss_per_flight_percent = VALUES(condition_loss_per_flight_percent),
  condition_warning_threshold_percent = VALUES(condition_warning_threshold_percent),
  condition_grounding_threshold_percent = VALUES(condition_grounding_threshold_percent),
  minor_fault_probability_percent = VALUES(minor_fault_probability_percent),
  major_fault_probability_percent = VALUES(major_fault_probability_percent),
  in_flight_fault_probability_percent = VALUES(in_flight_fault_probability_percent),
  routine_maintenance_duration_hours = VALUES(routine_maintenance_duration_hours),
  minor_repair_duration_hours = VALUES(minor_repair_duration_hours),
  major_repair_duration_hours = VALUES(major_repair_duration_hours),
  technician_license_required = VALUES(technician_license_required);

CREATE OR REPLACE VIEW v_mailbox_messages AS
SELECT
  m.id AS message_id,
  m.company_id,
  co.company_name,
  m.message_type,
  m.severity,
  m.status,
  m.title,
  m.body,
  m.related_entity_type,
  m.related_entity_id,
  m.action_payload_json,
  m.created_at_utc,
  m.read_at_utc,
  m.resolved_at_utc
FROM game_mailbox_messages m
JOIN companies co
  ON co.id = m.company_id;

CREATE OR REPLACE VIEW v_aircraft_maintenance_status AS
SELECT
  ca.id AS aircraft_id,
  ca.company_id,
  co.company_name,
  ca.registration_code,
  ca.status AS aircraft_status,
  ca.condition_percent,
  ca.airframe_hours,
  ca.cycles_count,
  ca.current_airport_icao_code,

  am.manufacturer,
  am.model_name,
  am.model_code,

  mp.routine_maintenance_interval_hours,
  mp.routine_maintenance_interval_cycles,
  mp.condition_loss_per_flight_percent,
  mp.condition_warning_threshold_percent,
  mp.condition_grounding_threshold_percent,
  mp.minor_fault_probability_percent,
  mp.major_fault_probability_percent,
  mp.in_flight_fault_probability_percent,
  mp.routine_maintenance_duration_hours,
  mp.minor_repair_duration_hours,
  mp.major_repair_duration_hours,
  mp.technician_license_required,

  CASE
    WHEN ca.condition_percent <= mp.condition_grounding_threshold_percent THEN 'GROUNDED_REQUIRED'
    WHEN ca.condition_percent <= mp.condition_warning_threshold_percent THEN 'MAINTENANCE_WARNING'
    WHEN ca.airframe_hours >= mp.routine_maintenance_interval_hours THEN 'ROUTINE_HOURS_DUE'
    WHEN ca.cycles_count >= mp.routine_maintenance_interval_cycles THEN 'ROUTINE_CYCLES_DUE'
    ELSE 'OK'
  END AS maintenance_state

FROM company_aircraft ca
JOIN companies co
  ON co.id = ca.company_id
JOIN aircraft_models am
  ON am.id = ca.aircraft_model_id
LEFT JOIN aircraft_maintenance_profiles mp
  ON mp.aircraft_model_id = am.id;

COMMIT;
