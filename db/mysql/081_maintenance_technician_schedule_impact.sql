-- Icaro Ops maintenance technician availability and schedule impact.
--
-- Purpose:
--   - assign a qualified technician to maintenance events
--   - calculate if maintenance overlaps the next scheduled route
--   - generate mailbox warning when maintenance causes delay/penalty risk
--
-- Run:
--   sudo mysql icaro_ops < db/mysql/081_maintenance_technician_schedule_impact.sql

USE icaro_ops;

START TRANSACTION;

ALTER TABLE aircraft_operational_events
  ADD COLUMN IF NOT EXISTS assigned_technician_id BIGINT UNSIGNED NULL AFTER required_technician_license,
  ADD COLUMN IF NOT EXISTS delay_risk_minutes INT UNSIGNED NOT NULL DEFAULT 0 AFTER assigned_technician_id,
  ADD COLUMN IF NOT EXISTS estimated_penalty_amount DECIMAL(15,2) NOT NULL DEFAULT 0.00 AFTER delay_risk_minutes,
  ADD COLUMN IF NOT EXISTS responsibility_type VARCHAR(40) NOT NULL DEFAULT 'COMPANY_FAULT' AFTER estimated_penalty_amount;

-- MariaDB does not support ADD CONSTRAINT IF NOT EXISTS, so keep this as a best-effort FK only if absent.
-- If the constraint already exists or your MariaDB version rejects duplicate names, ignore and continue manually.
-- ALTER TABLE aircraft_operational_events
--   ADD CONSTRAINT fk_aircraft_events_assigned_technician
--     FOREIGN KEY (assigned_technician_id)
--     REFERENCES company_staff(id)
--     ON UPDATE CASCADE
--     ON DELETE SET NULL;

CREATE OR REPLACE VIEW v_aircraft_maintenance_events_detail AS
SELECT
  e.id AS event_id,
  e.company_id,
  e.aircraft_id,
  ca.registration_code,
  e.event_type,
  e.severity,
  e.status,
  e.title,
  e.description,
  e.condition_percent_before,
  e.condition_percent_after,
  e.required_technician_license,
  e.assigned_technician_id,
  tech.display_name AS assigned_technician_name,
  e.delay_risk_minutes,
  e.estimated_penalty_amount,
  e.responsibility_type,
  e.started_at_utc,
  e.estimated_completed_at_utc,
  e.completed_at_utc,
  e.mailbox_message_id
FROM aircraft_operational_events e
JOIN company_aircraft ca
  ON ca.id = e.aircraft_id
LEFT JOIN company_staff tech
  ON tech.id = e.assigned_technician_id;

COMMIT;
