-- Icaro Ops - Maintenance costs for all aircraft models
-- Applies cost/duration data to every aircraft_models row and records maintenance expenses.
-- Safe to run more than once.

START TRANSACTION;

INSERT INTO staff_license_types (
  code,
  name,
  staff_role,
  description,
  is_required_for_commercial_ops,
  is_active
) VALUES (
  'CONC_MAINT',
  'Concorde Maintenance Qualification',
  'TECHNICIAN',
  'Specialized maintenance qualification for Aérospatiale/BAC Concorde.',
  1,
  1
)
ON DUPLICATE KEY UPDATE
  name = VALUES(name),
  staff_role = 'TECHNICIAN',
  description = VALUES(description),
  is_required_for_commercial_ops = 1,
  is_active = 1;

SET @sql := IF(
  (SELECT COUNT(*)
   FROM INFORMATION_SCHEMA.COLUMNS
   WHERE TABLE_SCHEMA = DATABASE()
     AND TABLE_NAME = 'aircraft_maintenance_profiles'
     AND COLUMN_NAME = 'routine_maintenance_cost_amount') = 0,
  'ALTER TABLE aircraft_maintenance_profiles ADD COLUMN routine_maintenance_cost_amount DECIMAL(15,2) NOT NULL DEFAULT 0.00 AFTER major_repair_duration_hours',
  'SELECT "aircraft_maintenance_profiles.routine_maintenance_cost_amount already exists"'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql := IF(
  (SELECT COUNT(*)
   FROM INFORMATION_SCHEMA.COLUMNS
   WHERE TABLE_SCHEMA = DATABASE()
     AND TABLE_NAME = 'aircraft_maintenance_profiles'
     AND COLUMN_NAME = 'minor_repair_cost_amount') = 0,
  'ALTER TABLE aircraft_maintenance_profiles ADD COLUMN minor_repair_cost_amount DECIMAL(15,2) NOT NULL DEFAULT 0.00 AFTER routine_maintenance_cost_amount',
  'SELECT "aircraft_maintenance_profiles.minor_repair_cost_amount already exists"'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql := IF(
  (SELECT COUNT(*)
   FROM INFORMATION_SCHEMA.COLUMNS
   WHERE TABLE_SCHEMA = DATABASE()
     AND TABLE_NAME = 'aircraft_maintenance_profiles'
     AND COLUMN_NAME = 'major_repair_cost_amount') = 0,
  'ALTER TABLE aircraft_maintenance_profiles ADD COLUMN major_repair_cost_amount DECIMAL(15,2) NOT NULL DEFAULT 0.00 AFTER minor_repair_cost_amount',
  'SELECT "aircraft_maintenance_profiles.major_repair_cost_amount already exists"'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql := IF(
  (SELECT COUNT(*)
   FROM INFORMATION_SCHEMA.COLUMNS
   WHERE TABLE_SCHEMA = DATABASE()
     AND TABLE_NAME = 'aircraft_operational_events'
     AND COLUMN_NAME = 'cost_amount') = 0,
  'ALTER TABLE aircraft_operational_events ADD COLUMN cost_amount DECIMAL(15,2) NOT NULL DEFAULT 0.00 AFTER estimated_penalty_amount',
  'SELECT "aircraft_operational_events.cost_amount already exists"'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql := IF(
  (SELECT COUNT(*)
   FROM INFORMATION_SCHEMA.COLUMNS
   WHERE TABLE_SCHEMA = DATABASE()
     AND TABLE_NAME = 'aircraft_operational_events'
     AND COLUMN_NAME = 'cost_currency_code') = 0,
  'ALTER TABLE aircraft_operational_events ADD COLUMN cost_currency_code CHAR(3) DEFAULT NULL AFTER cost_amount',
  'SELECT "aircraft_operational_events.cost_currency_code already exists"'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

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
  routine_maintenance_cost_amount,
  minor_repair_cost_amount,
  major_repair_cost_amount,
  technician_license_required
)
SELECT
  am.id,
  CASE
    WHEN am.icao_type_code = 'CONC' OR am.model_code IN ('CONCORDE', 'SSC_CONC') OR am.engine_type = 'SUPERSONIC' THEN 100
    WHEN am.max_takeoff_weight_kg >= 130000 OR am.passenger_capacity_standard >= 220 OR am.engine_count >= 4 THEN 140
    WHEN am.max_takeoff_weight_kg >= 70000 OR am.passenger_capacity_standard >= 120 THEN 120
    WHEN am.engine_type = 'TURBOFAN' THEN 110
    WHEN am.engine_type = 'TURBOPROP' AND (am.max_takeoff_weight_kg >= 10000 OR am.passenger_capacity_standard >= 20) THEN 130
    WHEN am.engine_type = 'TURBOPROP' THEN 120
    ELSE 100
  END AS routine_maintenance_interval_hours,
  CASE
    WHEN am.icao_type_code = 'CONC' OR am.model_code IN ('CONCORDE', 'SSC_CONC') OR am.engine_type = 'SUPERSONIC' THEN 60
    WHEN am.max_takeoff_weight_kg >= 130000 OR am.passenger_capacity_standard >= 220 OR am.engine_count >= 4 THEN 90
    WHEN am.max_takeoff_weight_kg >= 70000 OR am.passenger_capacity_standard >= 120 THEN 85
    WHEN am.engine_type = 'TURBOFAN' THEN 80
    WHEN am.engine_type = 'TURBOPROP' AND (am.max_takeoff_weight_kg >= 10000 OR am.passenger_capacity_standard >= 20) THEN 90
    WHEN am.engine_type = 'TURBOPROP' THEN 80
    ELSE 70
  END AS routine_maintenance_interval_cycles,
  CASE
    WHEN am.icao_type_code = 'CONC' OR am.model_code IN ('CONCORDE', 'SSC_CONC') OR am.engine_type = 'SUPERSONIC' THEN 0.90
    WHEN am.max_takeoff_weight_kg >= 130000 OR am.passenger_capacity_standard >= 220 OR am.engine_count >= 4 THEN 0.55
    WHEN am.max_takeoff_weight_kg >= 70000 OR am.passenger_capacity_standard >= 120 THEN 0.45
    WHEN am.engine_type = 'TURBOFAN' THEN 0.42
    WHEN am.engine_type = 'TURBOPROP' THEN 0.40
    ELSE 0.35
  END AS condition_loss_per_flight_percent,
  70.00,
  45.00,
  CASE
    WHEN am.icao_type_code = 'CONC' OR am.model_code IN ('CONCORDE', 'SSC_CONC') OR am.engine_type = 'SUPERSONIC' THEN 3.50
    WHEN am.max_takeoff_weight_kg >= 130000 OR am.passenger_capacity_standard >= 220 OR am.engine_count >= 4 THEN 1.80
    WHEN am.max_takeoff_weight_kg >= 70000 OR am.passenger_capacity_standard >= 120 THEN 1.40
    WHEN am.engine_type = 'TURBOFAN' THEN 1.25
    WHEN am.engine_type = 'TURBOPROP' THEN 1.10
    ELSE 1.00
  END AS minor_fault_probability_percent,
  CASE
    WHEN am.icao_type_code = 'CONC' OR am.model_code IN ('CONCORDE', 'SSC_CONC') OR am.engine_type = 'SUPERSONIC' THEN 1.50
    WHEN am.max_takeoff_weight_kg >= 130000 OR am.passenger_capacity_standard >= 220 OR am.engine_count >= 4 THEN 0.40
    WHEN am.max_takeoff_weight_kg >= 70000 OR am.passenger_capacity_standard >= 120 THEN 0.30
    WHEN am.engine_type = 'TURBOFAN' THEN 0.25
    ELSE 0.20
  END AS major_fault_probability_percent,
  CASE
    WHEN am.icao_type_code = 'CONC' OR am.model_code IN ('CONCORDE', 'SSC_CONC') OR am.engine_type = 'SUPERSONIC' THEN 0.40
    WHEN am.max_takeoff_weight_kg >= 130000 OR am.passenger_capacity_standard >= 220 OR am.engine_count >= 4 THEN 0.10
    WHEN am.max_takeoff_weight_kg >= 70000 OR am.passenger_capacity_standard >= 120 THEN 0.08
    ELSE 0.05
  END AS in_flight_fault_probability_percent,
  CASE
    WHEN am.icao_type_code = 'CONC' OR am.model_code IN ('CONCORDE', 'SSC_CONC') OR am.engine_type = 'SUPERSONIC' THEN 24
    WHEN am.max_takeoff_weight_kg >= 130000 OR am.passenger_capacity_standard >= 220 OR am.engine_count >= 4 THEN 12
    WHEN am.max_takeoff_weight_kg >= 70000 OR am.passenger_capacity_standard >= 120 THEN 8
    WHEN am.engine_type = 'TURBOFAN' THEN 6
    WHEN am.engine_type = 'TURBOPROP' AND (am.max_takeoff_weight_kg >= 10000 OR am.passenger_capacity_standard >= 20) THEN 5
    ELSE 3
  END AS routine_maintenance_duration_hours,
  CASE
    WHEN am.icao_type_code = 'CONC' OR am.model_code IN ('CONCORDE', 'SSC_CONC') OR am.engine_type = 'SUPERSONIC' THEN 48
    WHEN am.max_takeoff_weight_kg >= 130000 OR am.passenger_capacity_standard >= 220 OR am.engine_count >= 4 THEN 24
    WHEN am.max_takeoff_weight_kg >= 70000 OR am.passenger_capacity_standard >= 120 THEN 16
    WHEN am.engine_type = 'TURBOFAN' THEN 12
    WHEN am.engine_type = 'TURBOPROP' AND (am.max_takeoff_weight_kg >= 10000 OR am.passenger_capacity_standard >= 20) THEN 10
    ELSE 6
  END AS minor_repair_duration_hours,
  CASE
    WHEN am.icao_type_code = 'CONC' OR am.model_code IN ('CONCORDE', 'SSC_CONC') OR am.engine_type = 'SUPERSONIC' THEN 120
    WHEN am.max_takeoff_weight_kg >= 130000 OR am.passenger_capacity_standard >= 220 OR am.engine_count >= 4 THEN 72
    WHEN am.max_takeoff_weight_kg >= 70000 OR am.passenger_capacity_standard >= 120 THEN 48
    WHEN am.engine_type = 'TURBOFAN' THEN 32
    WHEN am.engine_type = 'TURBOPROP' AND (am.max_takeoff_weight_kg >= 10000 OR am.passenger_capacity_standard >= 20) THEN 28
    ELSE 18
  END AS major_repair_duration_hours,
  CASE
    WHEN am.icao_type_code = 'CONC' OR am.model_code IN ('CONCORDE', 'SSC_CONC') OR am.engine_type = 'SUPERSONIC' THEN 250000.00
    WHEN am.max_takeoff_weight_kg >= 130000 OR am.passenger_capacity_standard >= 220 OR am.engine_count >= 4 THEN 35000.00
    WHEN am.max_takeoff_weight_kg >= 70000 OR am.passenger_capacity_standard >= 120 THEN 15000.00
    WHEN am.engine_type = 'TURBOFAN' THEN 8000.00
    WHEN am.engine_type = 'TURBOPROP' AND (am.max_takeoff_weight_kg >= 10000 OR am.passenger_capacity_standard >= 20) THEN 5000.00
    WHEN am.engine_type = 'TURBOPROP' THEN 2500.00
    ELSE 1500.00
  END AS routine_maintenance_cost_amount,
  CASE
    WHEN am.icao_type_code = 'CONC' OR am.model_code IN ('CONCORDE', 'SSC_CONC') OR am.engine_type = 'SUPERSONIC' THEN 750000.00
    WHEN am.max_takeoff_weight_kg >= 130000 OR am.passenger_capacity_standard >= 220 OR am.engine_count >= 4 THEN 120000.00
    WHEN am.max_takeoff_weight_kg >= 70000 OR am.passenger_capacity_standard >= 120 THEN 55000.00
    WHEN am.engine_type = 'TURBOFAN' THEN 25000.00
    WHEN am.engine_type = 'TURBOPROP' AND (am.max_takeoff_weight_kg >= 10000 OR am.passenger_capacity_standard >= 20) THEN 18000.00
    WHEN am.engine_type = 'TURBOPROP' THEN 8000.00
    ELSE 5000.00
  END AS minor_repair_cost_amount,
  CASE
    WHEN am.icao_type_code = 'CONC' OR am.model_code IN ('CONCORDE', 'SSC_CONC') OR am.engine_type = 'SUPERSONIC' THEN 2500000.00
    WHEN am.max_takeoff_weight_kg >= 130000 OR am.passenger_capacity_standard >= 220 OR am.engine_count >= 4 THEN 400000.00
    WHEN am.max_takeoff_weight_kg >= 70000 OR am.passenger_capacity_standard >= 120 THEN 180000.00
    WHEN am.engine_type = 'TURBOFAN' THEN 90000.00
    WHEN am.engine_type = 'TURBOPROP' AND (am.max_takeoff_weight_kg >= 10000 OR am.passenger_capacity_standard >= 20) THEN 60000.00
    WHEN am.engine_type = 'TURBOPROP' THEN 25000.00
    ELSE 18000.00
  END AS major_repair_cost_amount,
  CASE
    WHEN am.icao_type_code = 'CONC' OR am.model_code IN ('CONCORDE', 'SSC_CONC') OR am.engine_type = 'SUPERSONIC' THEN 'CONC_MAINT'
    WHEN am.model_code LIKE 'C208%' THEN 'C208_MAINT'
    WHEN am.engine_type = 'TURBOPROP' THEN 'TURBOPROP_MAINT'
    ELSE 'A_AND_P'
  END AS technician_license_required
FROM aircraft_models am
ON DUPLICATE KEY UPDATE
  routine_maintenance_interval_hours = VALUES(routine_maintenance_interval_hours),
  routine_maintenance_interval_cycles = VALUES(routine_maintenance_interval_cycles),
  condition_loss_per_flight_percent = VALUES(condition_loss_per_flight_percent),
  minor_fault_probability_percent = VALUES(minor_fault_probability_percent),
  major_fault_probability_percent = VALUES(major_fault_probability_percent),
  in_flight_fault_probability_percent = VALUES(in_flight_fault_probability_percent),
  routine_maintenance_duration_hours = VALUES(routine_maintenance_duration_hours),
  minor_repair_duration_hours = VALUES(minor_repair_duration_hours),
  major_repair_duration_hours = VALUES(major_repair_duration_hours),
  routine_maintenance_cost_amount = VALUES(routine_maintenance_cost_amount),
  minor_repair_cost_amount = VALUES(minor_repair_cost_amount),
  major_repair_cost_amount = VALUES(major_repair_cost_amount),
  technician_license_required = CASE
    WHEN aircraft_maintenance_profiles.technician_license_required IS NULL
      OR aircraft_maintenance_profiles.technician_license_required = ''
    THEN VALUES(technician_license_required)
    ELSE aircraft_maintenance_profiles.technician_license_required
  END;

CREATE OR REPLACE VIEW v_company_aircraft_maintenance_detail AS
SELECT
  ca.id AS aircraft_id,
  ca.company_id AS company_id,
  co.company_name AS company_name,
  ca.registration_code AS registration_code,
  ca.serial_number AS serial_number,
  ca.manufacture_year AS manufacture_year,
  ca.ownership_status AS ownership_status,
  ca.acquisition_type AS acquisition_type,
  ca.purchase_price AS purchase_price,
  ca.current_market_value AS current_market_value,
  co.currency_code AS currency_code,
  ca.home_base_icao_code AS home_base_icao_code,
  hb.name AS home_base_name,
  ca.current_airport_icao_code AS current_airport_icao_code,
  cb.name AS current_airport_name,
  ca.condition_percent AS condition_percent,
  ca.airframe_hours AS airframe_hours,
  ca.cycles_count AS cycles_count,
  ca.status AS aircraft_status,
  am.id AS aircraft_model_id,
  am.manufacturer AS manufacturer,
  am.model_name AS model_name,
  am.model_code AS model_code,
  am.icao_type_code AS icao_type_code,
  am.operation_role AS operation_role,
  am.passenger_capacity_standard AS passenger_capacity_standard,
  am.range_km AS range_km,
  am.cruise_speed_kmh AS cruise_speed_kmh,
  am.image_asset_path AS image_asset_path,
  mp.routine_maintenance_interval_hours AS routine_maintenance_interval_hours,
  mp.routine_maintenance_interval_cycles AS routine_maintenance_interval_cycles,
  mp.condition_loss_per_flight_percent AS condition_loss_per_flight_percent,
  mp.condition_warning_threshold_percent AS condition_warning_threshold_percent,
  mp.condition_grounding_threshold_percent AS condition_grounding_threshold_percent,
  mp.routine_maintenance_duration_hours AS routine_maintenance_duration_hours,
  mp.minor_repair_duration_hours AS minor_repair_duration_hours,
  mp.major_repair_duration_hours AS major_repair_duration_hours,
  mp.routine_maintenance_cost_amount AS routine_maintenance_cost_amount,
  mp.minor_repair_cost_amount AS minor_repair_cost_amount,
  mp.major_repair_cost_amount AS major_repair_cost_amount,
  mp.technician_license_required AS technician_license_required,
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
    SELECT COUNT(0)
    FROM aircraft_operational_events e
    WHERE e.aircraft_id = ca.id
      AND e.status IN ('OPEN','IN_PROGRESS')
  ) AS open_event_count
FROM company_aircraft ca
JOIN companies co ON co.id = ca.company_id
JOIN airports hb ON hb.icao_code = ca.home_base_icao_code
JOIN airports cb ON cb.icao_code = ca.current_airport_icao_code
JOIN aircraft_models am ON am.id = ca.aircraft_model_id
LEFT JOIN aircraft_maintenance_profiles mp ON mp.aircraft_model_id = am.id;

UPDATE aircraft_operational_events e
JOIN companies c ON c.id = e.company_id
SET e.cost_currency_code = c.currency_code
WHERE e.cost_currency_code IS NULL;

COMMIT;

SELECT
  (SELECT COUNT(*) FROM aircraft_models) AS aircraft_models_total,
  (SELECT COUNT(*) FROM aircraft_maintenance_profiles) AS maintenance_profiles_total,
  (SELECT COUNT(*)
   FROM aircraft_models am
   LEFT JOIN aircraft_maintenance_profiles mp ON mp.aircraft_model_id = am.id
   WHERE mp.aircraft_model_id IS NULL) AS missing_profiles,
  (SELECT COUNT(*)
   FROM aircraft_maintenance_profiles
   WHERE routine_maintenance_cost_amount <= 0
      OR minor_repair_cost_amount <= 0
      OR major_repair_cost_amount <= 0) AS profiles_without_costs;
