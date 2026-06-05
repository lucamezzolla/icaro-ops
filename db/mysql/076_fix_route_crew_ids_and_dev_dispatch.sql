USE icaro_ops;

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

  r.assigned_pilot_1_id,
  r.assigned_pilot_2_id,
  r.assigned_technician_id,

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
