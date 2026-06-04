-- Icaro Ops Rome/Ciampino base and search fix.
--
-- Purpose:
--   The Europe import currently has many Italian airports without coordinates.
--   Without coordinates, LIRA/Ciampino cannot appear on the map and may be excluded
--   from the starting-base view.
--
-- Run:
--   sudo mysql icaro_ops < db/mysql/064_fix_rome_base_airport_coordinates.sql

USE icaro_ops;

START TRANSACTION;

-- Rome Ciampino / G. B. Pastine
UPDATE airports
SET
  latitude = 41.7994000,
  longitude = 12.5949000,
  elevation_ft = COALESCE(elevation_ft, 427),
  airport_type = 'AIRPORT',
  service_category = 'NATIONAL',
  is_civilian = TRUE,
  is_commercial = TRUE,
  is_military = FALSE,
  is_closed = FALSE,
  data_quality = CASE
    WHEN data_quality IS NULL OR data_quality = 'PARTIAL' THEN 'PARTIAL'
    ELSE data_quality
  END
WHERE icao_code = 'LIRA';

-- Rome Fiumicino is intentionally not suitable as a novice base, but coordinates
-- are useful for map/search correctness.
UPDATE airports
SET
  latitude = 41.8003000,
  longitude = 12.2389000,
  elevation_ft = COALESCE(elevation_ft, 13),
  airport_type = 'AIRPORT',
  service_category = 'INTERNATIONAL',
  is_civilian = TRUE,
  is_commercial = TRUE,
  is_military = FALSE,
  is_closed = FALSE
WHERE icao_code = 'LIRF';

-- Force Ciampino to be selectable as a small starting base candidate.
INSERT INTO airport_starting_base_overrides (
  airport_icao_code,
  force_eligible,
  base_tier_override,
  max_initial_aircraft_class_override,
  starting_base_score_override,
  note
)
SELECT
  'LIRA',
  TRUE,
  'REGIONAL',
  'LIGHT_COMMERCIAL',
  78,
  'Manual override: Rome Ciampino is suitable for early small commercial operations.'
FROM airports
WHERE icao_code = 'LIRA'
ON DUPLICATE KEY UPDATE
  force_eligible = VALUES(force_eligible),
  base_tier_override = VALUES(base_tier_override),
  max_initial_aircraft_class_override = VALUES(max_initial_aircraft_class_override),
  starting_base_score_override = VALUES(starting_base_score_override),
  note = VALUES(note);

-- Keep Fiumicino explicitly blocked from novice starts.
INSERT INTO airport_starting_base_blacklist (
  airport_icao_code,
  reason
)
SELECT
  'LIRF',
  'Large international hub; not suitable for novice small-aircraft operations.'
FROM airports
WHERE icao_code = 'LIRF'
ON DUPLICATE KEY UPDATE
  reason = VALUES(reason);

SELECT
  icao_code,
  iata_code,
  name,
  city,
  latitude,
  longitude,
  service_category,
  is_closed
FROM airports
WHERE icao_code IN ('LIRA', 'LIRF')
ORDER BY icao_code;

SELECT
  icao_code,
  airport_name,
  city,
  country_name,
  latitude,
  longitude,
  base_tier,
  starting_base_score
FROM v_starting_base_airports
WHERE icao_code = 'LIRA';

COMMIT;
