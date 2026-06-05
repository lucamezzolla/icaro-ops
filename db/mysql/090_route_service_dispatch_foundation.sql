USE icaro_ops;

START TRANSACTION;

CREATE TABLE IF NOT EXISTS air_routes (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  route_code VARCHAR(80) NOT NULL,
  origin_airport_icao_code CHAR(4) NOT NULL,
  destination_airport_icao_code CHAR(4) NOT NULL,
  route_scope VARCHAR(30) NOT NULL DEFAULT 'DOMESTIC',
  route_market VARCHAR(30) NOT NULL DEFAULT 'PAX',
  route_operation_domain VARCHAR(30) NOT NULL DEFAULT 'CIVIL',
  required_aircraft_class VARCHAR(40) NOT NULL DEFAULT 'LIGHT_COMMERCIAL',
  min_passenger_capacity SMALLINT UNSIGNED NULL,
  max_passenger_capacity SMALLINT UNSIGNED NULL,
  min_range_km DECIMAL(10,2) NULL,
  required_runway_m INT UNSIGNED NULL,
  planned_distance_km DECIMAL(10,2) NOT NULL,
  estimated_block_minutes INT UNSIGNED NOT NULL,
  status VARCHAR(30) NOT NULL DEFAULT 'ACTIVE',
  created_at_utc TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at_utc TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_air_routes_route_code (route_code),
  UNIQUE KEY uq_air_routes_natural (
    origin_airport_icao_code,
    destination_airport_icao_code,
    route_scope,
    route_market,
    route_operation_domain,
    required_aircraft_class
  ),
  KEY idx_air_routes_origin_destination (origin_airport_icao_code, destination_airport_icao_code),
  KEY idx_air_routes_scope_market (route_scope, route_market, status),
  CONSTRAINT fk_air_routes_origin FOREIGN KEY (origin_airport_icao_code)
    REFERENCES airports(icao_code) ON UPDATE CASCADE ON DELETE RESTRICT,
  CONSTRAINT fk_air_routes_destination FOREIGN KEY (destination_airport_icao_code)
    REFERENCES airports(icao_code) ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS scheduled_services (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  company_id BIGINT UNSIGNED NOT NULL,
  air_route_id BIGINT UNSIGNED NOT NULL,
  service_code VARCHAR(80) NOT NULL,
  recurrence_type VARCHAR(30) NOT NULL DEFAULT 'DAILY',
  scheduled_departure_time_utc TIME NOT NULL,
  service_status VARCHAR(30) NOT NULL DEFAULT 'ACTIVE',
  preferred_aircraft_model_id BIGINT UNSIGNED NULL,
  required_aircraft_class VARCHAR(40) NOT NULL DEFAULT 'LIGHT_COMMERCIAL',
  base_ticket_price DECIMAL(12,2) NULL,
  currency_code CHAR(3) NOT NULL DEFAULT 'EUR',
  auto_dispatch_enabled TINYINT(1) NOT NULL DEFAULT 1,
  allow_backup_aircraft TINYINT(1) NOT NULL DEFAULT 1,
  allow_extra_flights TINYINT(1) NOT NULL DEFAULT 1,
  created_at_utc TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at_utc TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_scheduled_services_code (service_code),
  KEY idx_scheduled_services_company_status (company_id, service_status),
  KEY idx_scheduled_services_route (air_route_id),
  KEY idx_scheduled_services_departure (scheduled_departure_time_utc),
  CONSTRAINT fk_scheduled_services_company FOREIGN KEY (company_id)
    REFERENCES companies(id) ON UPDATE CASCADE ON DELETE CASCADE,
  CONSTRAINT fk_scheduled_services_air_route FOREIGN KEY (air_route_id)
    REFERENCES air_routes(id) ON UPDATE CASCADE ON DELETE RESTRICT,
  CONSTRAINT fk_scheduled_services_preferred_model FOREIGN KEY (preferred_aircraft_model_id)
    REFERENCES aircraft_models(id) ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS flight_dispatch_requirements (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  scheduled_service_id BIGINT UNSIGNED NULL,
  scheduled_flight_instance_id BIGINT UNSIGNED NULL,
  required_aircraft_class VARCHAR(40) NOT NULL DEFAULT 'LIGHT_COMMERCIAL',
  preferred_aircraft_model_id BIGINT UNSIGNED NULL,
  required_aircraft_model_id BIGINT UNSIGNED NULL,
  min_passenger_capacity SMALLINT UNSIGNED NULL,
  max_passenger_capacity SMALLINT UNSIGNED NULL,
  min_range_km DECIMAL(10,2) NULL,
  required_origin_airport_icao_code CHAR(4) NOT NULL,
  allow_same_model_backup TINYINT(1) NOT NULL DEFAULT 1,
  allow_compatible_model_backup TINYINT(1) NOT NULL DEFAULT 1,
  created_at_utc TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_fdr_service (scheduled_service_id),
  KEY idx_fdr_flight (scheduled_flight_instance_id),
  KEY idx_fdr_origin (required_origin_airport_icao_code),
  CONSTRAINT fk_fdr_service FOREIGN KEY (scheduled_service_id)
    REFERENCES scheduled_services(id) ON UPDATE CASCADE ON DELETE CASCADE,
  CONSTRAINT fk_fdr_flight FOREIGN KEY (scheduled_flight_instance_id)
    REFERENCES scheduled_flight_instances(id) ON UPDATE CASCADE ON DELETE CASCADE,
  CONSTRAINT fk_fdr_preferred_model FOREIGN KEY (preferred_aircraft_model_id)
    REFERENCES aircraft_models(id) ON UPDATE CASCADE ON DELETE SET NULL,
  CONSTRAINT fk_fdr_required_model FOREIGN KEY (required_aircraft_model_id)
    REFERENCES aircraft_models(id) ON UPDATE CASCADE ON DELETE SET NULL,
  CONSTRAINT fk_fdr_origin_airport FOREIGN KEY (required_origin_airport_icao_code)
    REFERENCES airports(icao_code) ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

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
  ADD COLUMN IF NOT EXISTS schedule_conflict_status VARCHAR(30) NOT NULL DEFAULT 'NONE' AFTER backup_reason,
  ADD COLUMN IF NOT EXISTS requires_return_to_airport_icao_code CHAR(4) NULL AFTER schedule_conflict_status,
  ADD COLUMN IF NOT EXISTS required_back_at_utc DATETIME NULL AFTER requires_return_to_airport_icao_code;

INSERT IGNORE INTO air_routes (
  route_code, origin_airport_icao_code, destination_airport_icao_code,
  route_scope, route_market, route_operation_domain, required_aircraft_class,
  min_passenger_capacity, max_passenger_capacity, min_range_km,
  planned_distance_km, estimated_block_minutes, status
)
SELECT
  CONCAT('AR-', cr.origin_airport_icao_code, '-', cr.destination_airport_icao_code, '-DOM-PAX'),
  cr.origin_airport_icao_code,
  cr.destination_airport_icao_code,
  'DOMESTIC',
  'PAX',
  'CIVIL',
  'LIGHT_COMMERCIAL',
  1,
  19,
  cr.planned_distance_km,
  cr.planned_distance_km,
  cr.planned_duration_minutes,
  'ACTIVE'
FROM company_routes cr
WHERE NOT EXISTS (
  SELECT 1 FROM air_routes ar
  WHERE ar.origin_airport_icao_code = cr.origin_airport_icao_code
    AND ar.destination_airport_icao_code = cr.destination_airport_icao_code
    AND ar.route_scope = 'DOMESTIC'
    AND ar.route_market = 'PAX'
    AND ar.route_operation_domain = 'CIVIL'
    AND ar.required_aircraft_class = 'LIGHT_COMMERCIAL'
);

INSERT IGNORE INTO scheduled_services (
  company_id, air_route_id, service_code, recurrence_type,
  scheduled_departure_time_utc, service_status, preferred_aircraft_model_id,
  required_aircraft_class, base_ticket_price, currency_code,
  auto_dispatch_enabled, allow_backup_aircraft, allow_extra_flights
)
SELECT
  cr.company_id,
  ar.id,
  CONCAT('SV-C', LPAD(cr.company_id, 3, '0'), '-', cr.origin_airport_icao_code, '-', cr.destination_airport_icao_code, '-', REPLACE(LEFT(cr.scheduled_departure_time_utc, 5), ':', '')),
  cr.recurrence_type,
  cr.scheduled_departure_time_utc,
  cr.status,
  ca.aircraft_model_id,
  'LIGHT_COMMERCIAL',
  cr.ticket_price,
  cr.currency_code,
  1,
  1,
  1
FROM company_routes cr
JOIN air_routes ar
  ON ar.origin_airport_icao_code = cr.origin_airport_icao_code
 AND ar.destination_airport_icao_code = cr.destination_airport_icao_code
 AND ar.route_scope = 'DOMESTIC'
 AND ar.route_market = 'PAX'
 AND ar.route_operation_domain = 'CIVIL'
 AND ar.required_aircraft_class = 'LIGHT_COMMERCIAL'
LEFT JOIN company_aircraft ca ON ca.id = cr.aircraft_id
WHERE NOT EXISTS (
  SELECT 1 FROM scheduled_services ss
  WHERE ss.company_id = cr.company_id
    AND ss.air_route_id = ar.id
    AND ss.scheduled_departure_time_utc = cr.scheduled_departure_time_utc
);

UPDATE scheduled_flight_instances f
JOIN company_routes cr ON cr.id = f.route_id
JOIN air_routes ar
  ON ar.origin_airport_icao_code = cr.origin_airport_icao_code
 AND ar.destination_airport_icao_code = cr.destination_airport_icao_code
 AND ar.route_scope = 'DOMESTIC'
 AND ar.route_market = 'PAX'
 AND ar.route_operation_domain = 'CIVIL'
 AND ar.required_aircraft_class = 'LIGHT_COMMERCIAL'
LEFT JOIN scheduled_services ss
  ON ss.company_id = f.company_id
 AND ss.air_route_id = ar.id
 AND ss.scheduled_departure_time_utc = cr.scheduled_departure_time_utc
SET
  f.air_route_id = ar.id,
  f.scheduled_service_id = ss.id,
  f.flight_operation_type = 'SCHEDULED',
  f.required_aircraft_class = 'LIGHT_COMMERCIAL',
  f.preferred_aircraft_model_id = ss.preferred_aircraft_model_id,
  f.planned_aircraft_id = f.aircraft_id,
  f.dispatch_aircraft_id = f.aircraft_id,
  f.dispatch_status = CASE WHEN f.aircraft_id IS NOT NULL THEN 'ASSIGNED' ELSE 'PENDING' END
WHERE f.air_route_id IS NULL;

UPDATE companies
SET budget_amount = GREATEST(budget_amount, 8500000.00)
WHERE budget_amount < 8500000.00
  AND id IN (SELECT company_id FROM players);

COMMIT;

SELECT 'Route/service/dispatch foundation installed' AS result;
