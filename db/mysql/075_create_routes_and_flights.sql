-- Icaro Ops routes and first scheduled flight simulation.
--
-- Purpose:
--   Add company routes and scheduled flight instances.
--
-- First gameplay target:
--   LIRA -> LIML at 10:00 UTC with a Cessna 208B.
--
-- Dispatch requirements for C208 passenger operations:
--   - 1 available/parked company aircraft assigned to the route
--   - 2 active pilots with CPL + C208_TYPE
--   - 1 active technician with C208_MAINT
--
-- Run:
--   sudo mysql icaro_ops < db/mysql/075_create_routes_and_flights.sql

USE icaro_ops;

START TRANSACTION;

-- Ensure LIRA and LIML have coordinates for the first simulation.
-- These values are development seed coordinates and should be periodically reviewed
-- together with the airport master data.
UPDATE airports
SET
  latitude = COALESCE(latitude, 41.79940),
  longitude = COALESCE(longitude, 12.59490)
WHERE icao_code = 'LIRA';

UPDATE airports
SET
  latitude = COALESCE(latitude, 45.44510),
  longitude = COALESCE(longitude, 9.27670)
WHERE icao_code = 'LIML';

CREATE TABLE IF NOT EXISTS company_routes (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,

  company_id BIGINT UNSIGNED NOT NULL,
  aircraft_id BIGINT UNSIGNED NOT NULL,

  origin_airport_icao_code CHAR(4) NOT NULL,
  destination_airport_icao_code CHAR(4) NOT NULL,

  scheduled_departure_time_utc TIME NOT NULL,
  recurrence_type VARCHAR(20) NOT NULL DEFAULT 'DAILY',

  assigned_pilot_1_id BIGINT UNSIGNED NOT NULL,
  assigned_pilot_2_id BIGINT UNSIGNED NOT NULL,
  assigned_technician_id BIGINT UNSIGNED NOT NULL,

  planned_distance_km DECIMAL(10,2) NOT NULL,
  planned_duration_minutes INT UNSIGNED NOT NULL,

  ticket_price DECIMAL(12,2) NOT NULL DEFAULT 145.00,
  currency_code CHAR(3) NOT NULL DEFAULT 'EUR',

  status VARCHAR(30) NOT NULL DEFAULT 'ACTIVE',

  created_at_utc TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at_utc TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

  PRIMARY KEY (id),
  KEY idx_company_routes_company_status (company_id, status),
  KEY idx_company_routes_aircraft (aircraft_id),
  KEY idx_company_routes_origin_destination (origin_airport_icao_code, destination_airport_icao_code),

  CONSTRAINT fk_company_routes_company
    FOREIGN KEY (company_id)
    REFERENCES companies(id)
    ON UPDATE CASCADE
    ON DELETE CASCADE,

  CONSTRAINT fk_company_routes_aircraft
    FOREIGN KEY (aircraft_id)
    REFERENCES company_aircraft(id)
    ON UPDATE CASCADE
    ON DELETE RESTRICT,

  CONSTRAINT fk_company_routes_origin
    FOREIGN KEY (origin_airport_icao_code)
    REFERENCES airports(icao_code)
    ON UPDATE CASCADE
    ON DELETE RESTRICT,

  CONSTRAINT fk_company_routes_destination
    FOREIGN KEY (destination_airport_icao_code)
    REFERENCES airports(icao_code)
    ON UPDATE CASCADE
    ON DELETE RESTRICT,

  CONSTRAINT fk_company_routes_pilot_1
    FOREIGN KEY (assigned_pilot_1_id)
    REFERENCES company_staff(id)
    ON UPDATE CASCADE
    ON DELETE RESTRICT,

  CONSTRAINT fk_company_routes_pilot_2
    FOREIGN KEY (assigned_pilot_2_id)
    REFERENCES company_staff(id)
    ON UPDATE CASCADE
    ON DELETE RESTRICT,

  CONSTRAINT fk_company_routes_technician
    FOREIGN KEY (assigned_technician_id)
    REFERENCES company_staff(id)
    ON UPDATE CASCADE
    ON DELETE RESTRICT,

  CONSTRAINT chk_company_routes_recurrence
    CHECK (recurrence_type IN ('DAILY')),

  CONSTRAINT chk_company_routes_status
    CHECK (status IN ('ACTIVE', 'PAUSED', 'CANCELLED')),

  CONSTRAINT chk_company_routes_amounts
    CHECK (
      planned_distance_km > 0
      AND planned_duration_minutes > 0
      AND ticket_price >= 0
    )
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS scheduled_flight_instances (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,

  route_id BIGINT UNSIGNED NOT NULL,
  company_id BIGINT UNSIGNED NOT NULL,
  aircraft_id BIGINT UNSIGNED NOT NULL,

  flight_code VARCHAR(30) NOT NULL,
  flight_date_utc DATE NOT NULL,

  origin_airport_icao_code CHAR(4) NOT NULL,
  destination_airport_icao_code CHAR(4) NOT NULL,

  scheduled_departure_at_utc DATETIME NOT NULL,
  scheduled_arrival_at_utc DATETIME NOT NULL,
  actual_departure_at_utc DATETIME NULL,
  actual_arrival_at_utc DATETIME NULL,

  status VARCHAR(30) NOT NULL DEFAULT 'SCHEDULED',

  passenger_capacity SMALLINT UNSIGNED NOT NULL,
  passenger_count SMALLINT UNSIGNED NOT NULL DEFAULT 0,
  load_factor_percent DECIMAL(5,2) NOT NULL DEFAULT 0.00,

  ticket_price DECIMAL(12,2) NOT NULL DEFAULT 0.00,
  passenger_revenue DECIMAL(15,2) NOT NULL DEFAULT 0.00,
  fuel_cost DECIMAL(15,2) NOT NULL DEFAULT 0.00,
  maintenance_cost DECIMAL(15,2) NOT NULL DEFAULT 0.00,
  staff_cost DECIMAL(15,2) NOT NULL DEFAULT 0.00,
  total_operating_cost DECIMAL(15,2) NOT NULL DEFAULT 0.00,
  profit_amount DECIMAL(15,2) NOT NULL DEFAULT 0.00,
  currency_code CHAR(3) NOT NULL DEFAULT 'EUR',

  created_at_utc TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at_utc TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

  PRIMARY KEY (id),
  UNIQUE KEY uk_scheduled_flight_route_date (route_id, flight_date_utc),
  KEY idx_scheduled_flight_company_status (company_id, status),
  KEY idx_scheduled_flight_aircraft_status (aircraft_id, status),
  KEY idx_scheduled_flight_arrival (status, scheduled_arrival_at_utc),

  CONSTRAINT fk_scheduled_flight_route
    FOREIGN KEY (route_id)
    REFERENCES company_routes(id)
    ON UPDATE CASCADE
    ON DELETE CASCADE,

  CONSTRAINT fk_scheduled_flight_company
    FOREIGN KEY (company_id)
    REFERENCES companies(id)
    ON UPDATE CASCADE
    ON DELETE CASCADE,

  CONSTRAINT fk_scheduled_flight_aircraft
    FOREIGN KEY (aircraft_id)
    REFERENCES company_aircraft(id)
    ON UPDATE CASCADE
    ON DELETE RESTRICT,

  CONSTRAINT fk_scheduled_flight_origin
    FOREIGN KEY (origin_airport_icao_code)
    REFERENCES airports(icao_code)
    ON UPDATE CASCADE
    ON DELETE RESTRICT,

  CONSTRAINT fk_scheduled_flight_destination
    FOREIGN KEY (destination_airport_icao_code)
    REFERENCES airports(icao_code)
    ON UPDATE CASCADE
    ON DELETE RESTRICT,

  CONSTRAINT chk_scheduled_flight_status
    CHECK (status IN ('SCHEDULED', 'IN_FLIGHT', 'COMPLETED', 'CANCELLED')),

  CONSTRAINT chk_scheduled_flight_amounts
    CHECK (
      passenger_capacity >= passenger_count
      AND load_factor_percent BETWEEN 0 AND 100
      AND ticket_price >= 0
      AND passenger_revenue >= 0
      AND fuel_cost >= 0
      AND maintenance_cost >= 0
      AND staff_cost >= 0
      AND total_operating_cost >= 0
    )
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
  r.planned_distance_km,
  r.planned_duration_minutes,
  r.ticket_price,
  r.currency_code,
  r.status,

  p1.display_name AS pilot_1_name,
  p2.display_name AS pilot_2_name,
  tech.display_name AS technician_name

FROM company_routes r
JOIN companies co
  ON co.id = r.company_id
JOIN company_aircraft ca
  ON ca.id = r.aircraft_id
JOIN aircraft_models am
  ON am.id = ca.aircraft_model_id
JOIN airports oa
  ON oa.icao_code = r.origin_airport_icao_code
JOIN airports da
  ON da.icao_code = r.destination_airport_icao_code
JOIN company_staff p1
  ON p1.id = r.assigned_pilot_1_id
JOIN company_staff p2
  ON p2.id = r.assigned_pilot_2_id
JOIN company_staff tech
  ON tech.id = r.assigned_technician_id;

CREATE OR REPLACE VIEW v_active_flights_map AS
SELECT
  f.id AS flight_instance_id,
  f.route_id,
  f.company_id,
  co.company_name,
  f.aircraft_id,
  ca.registration_code,

  am.manufacturer,
  am.model_name,
  am.model_code,
  am.cruise_speed_kmh,

  f.flight_code,
  f.flight_date_utc,
  f.origin_airport_icao_code,
  oa.name AS origin_airport_name,
  oa.latitude AS origin_latitude,
  oa.longitude AS origin_longitude,

  f.destination_airport_icao_code,
  da.name AS destination_airport_name,
  da.latitude AS destination_latitude,
  da.longitude AS destination_longitude,

  f.scheduled_departure_at_utc,
  f.scheduled_arrival_at_utc,
  f.actual_departure_at_utc,
  f.status,
  f.passenger_capacity,
  f.passenger_count,
  f.load_factor_percent,
  f.passenger_revenue,
  f.total_operating_cost,
  f.profit_amount,
  f.currency_code,

  LEAST(
    100,
    GREATEST(
      0,
      TIMESTAMPDIFF(SECOND, f.actual_departure_at_utc, UTC_TIMESTAMP()) /
      NULLIF(TIMESTAMPDIFF(SECOND, f.actual_departure_at_utc, f.scheduled_arrival_at_utc), 0)
      * 100
    )
  ) AS progress_percent

FROM scheduled_flight_instances f
JOIN companies co
  ON co.id = f.company_id
JOIN company_aircraft ca
  ON ca.id = f.aircraft_id
JOIN aircraft_models am
  ON am.id = ca.aircraft_model_id
JOIN airports oa
  ON oa.icao_code = f.origin_airport_icao_code
JOIN airports da
  ON da.icao_code = f.destination_airport_icao_code
WHERE f.status = 'IN_FLIGHT';

SELECT 'Routes and flights schema ready' AS result;

COMMIT;
