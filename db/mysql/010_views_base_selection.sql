-- Views useful for the initial base selection UI.

USE icaro_ops;

CREATE OR REPLACE VIEW v_base_selection_regions AS
SELECT
  r.id AS region_id,
  r.region_code,
  r.name AS region_name,
  COUNT(DISTINCT p.id) AS prefix_count,
  COUNT(DISTINCT a.id) AS starter_airport_count
FROM icao_regions r
LEFT JOIN icao_prefixes p
  ON p.icao_region_id = r.id
 AND p.is_active = TRUE
LEFT JOIN airports a
  ON a.icao_prefix_id = p.id
LEFT JOIN airport_game_profiles gp
  ON gp.airport_id = a.id
 AND gp.starter_base_allowed = TRUE
WHERE r.is_active = TRUE
GROUP BY r.id, r.region_code, r.name;

CREATE OR REPLACE VIEW v_base_selection_airports AS
SELECT
  r.region_code,
  r.name AS region_name,
  p.prefix,
  p.country_name AS prefix_country_name,
  p.area_name AS prefix_area_name,
  a.id AS airport_id,
  a.icao_code,
  a.iata_code,
  a.name AS airport_name,
  a.city,
  a.country_name,
  a.subdivision_name,
  a.latitude,
  a.longitude,
  gp.airport_size,
  gp.starter_difficulty,
  gp.slot_cost_level,
  gp.passenger_demand_level,
  gp.cargo_demand_level,
  gp.max_aircraft_class
FROM airport_game_profiles gp
JOIN airports a
  ON a.id = gp.airport_id
JOIN icao_prefixes p
  ON p.id = a.icao_prefix_id
JOIN icao_regions r
  ON r.id = p.icao_region_id
WHERE gp.starter_base_allowed = TRUE
  AND a.is_closed = FALSE
  AND p.is_active = TRUE
  AND r.is_active = TRUE;
