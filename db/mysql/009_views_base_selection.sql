-- Views useful for the initial base selection UI.
-- User flow: region -> country -> airport.
-- Airports table is empty for now, so airport_count and starter_airport_count will be zero.

USE icaro_ops;

CREATE OR REPLACE VIEW v_base_selection_regions AS
SELECT
  r.code AS region_code,
  r.name AS region_name,
  COUNT(DISTINCT c.id) AS country_count,
  COUNT(DISTINCT a.icao_code) AS airport_count,
  SUM(CASE WHEN gp.starter_base_allowed = TRUE THEN 1 ELSE 0 END) AS starter_airport_count
FROM world_regions r
LEFT JOIN countries c
  ON c.world_region_code = r.code
 AND c.is_active = TRUE
LEFT JOIN airports a
  ON a.country_id = c.id
 AND a.is_closed = FALSE
LEFT JOIN airport_game_profiles gp
  ON gp.airport_icao_code = a.icao_code
WHERE r.is_active = TRUE
GROUP BY r.code, r.name;

CREATE OR REPLACE VIEW v_base_selection_countries AS
SELECT
  r.code AS region_code,
  r.name AS region_name,
  c.id AS country_id,
  c.name AS country_name,
  c.subregion_name,
  c.has_airports,
  COUNT(DISTINCT a.icao_code) AS airport_count,
  SUM(CASE WHEN gp.starter_base_allowed = TRUE THEN 1 ELSE 0 END) AS starter_airport_count
FROM countries c
JOIN world_regions r
  ON r.code = c.world_region_code
LEFT JOIN airports a
  ON a.country_id = c.id
 AND a.is_closed = FALSE
LEFT JOIN airport_game_profiles gp
  ON gp.airport_icao_code = a.icao_code
WHERE c.is_active = TRUE
  AND r.is_active = TRUE
GROUP BY
  r.code,
  r.name,
  c.id,
  c.name,
  c.subregion_name,
  c.has_airports;

CREATE OR REPLACE VIEW v_base_selection_airports AS
SELECT
  r.code AS region_code,
  r.name AS region_name,
  c.id AS country_id,
  c.name AS country_name,
  c.subregion_name,
  a.icao_code,
  a.icao_prefix,
  a.iata_code,
  a.name AS airport_name,
  a.city,
  a.location_name,
  a.subdivision_name,
  a.latitude,
  a.longitude,
  a.airport_type,
  a.operator_country_name,
  gp.airport_size,
  gp.starter_difficulty,
  gp.slot_cost_level,
  gp.passenger_demand_level,
  gp.cargo_demand_level,
  gp.max_aircraft_class
FROM airports a
JOIN countries c
  ON c.id = a.country_id
JOIN world_regions r
  ON r.code = c.world_region_code
LEFT JOIN airport_game_profiles gp
  ON gp.airport_icao_code = a.icao_code
WHERE a.is_closed = FALSE
  AND c.is_active = TRUE
  AND r.is_active = TRUE;
