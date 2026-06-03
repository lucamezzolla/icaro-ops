-- Starter airport game profiles.
-- These values are gameplay balancing values, not real-world facts.

USE icaro_ops;

INSERT INTO airport_game_profiles (
  airport_id,
  airport_size,
  starter_base_allowed,
  starter_difficulty,
  base_opening_cost,
  monthly_base_cost,
  slot_cost_level,
  passenger_demand_level,
  cargo_demand_level,
  max_aircraft_class,
  runway_category
) VALUES
((SELECT id FROM airports WHERE icao_code = 'LIRA'), 'SMALL_COMMERCIAL', TRUE, 'NORMAL', 0.00, 0.00, 'LOW', 'LOW', 'LOW', 'REGIONAL_JET', 'UNKNOWN'),
((SELECT id FROM airports WHERE icao_code = 'LIMJ'), 'SMALL_COMMERCIAL', TRUE, 'NORMAL', 0.00, 0.00, 'LOW', 'LOW', 'LOW', 'REGIONAL_JET', 'UNKNOWN'),
((SELECT id FROM airports WHERE icao_code = 'LICC'), 'SMALL_COMMERCIAL', TRUE, 'EASY', 0.00, 0.00, 'LOW', 'LOW', 'LOW', 'NARROW_BODY', 'UNKNOWN'),
((SELECT id FROM airports WHERE icao_code = 'EGTE'), 'SMALL_COMMERCIAL', TRUE, 'NORMAL', 0.00, 0.00, 'LOW', 'LOW', 'LOW', 'REGIONAL_JET', 'UNKNOWN'),
((SELECT id FROM airports WHERE icao_code = 'LFMD'), 'SMALL_COMMERCIAL', TRUE, 'HARD', 0.00, 0.00, 'LOW', 'LOW', 'LOW', 'TURBOPROP', 'UNKNOWN'),
((SELECT id FROM airports WHERE icao_code = 'EDFH'), 'SMALL_COMMERCIAL', TRUE, 'NORMAL', 0.00, 0.00, 'LOW', 'LOW', 'LOW', 'NARROW_BODY', 'UNKNOWN'),
((SELECT id FROM airports WHERE icao_code = 'LEST'), 'SMALL_COMMERCIAL', TRUE, 'NORMAL', 0.00, 0.00, 'LOW', 'LOW', 'LOW', 'NARROW_BODY', 'UNKNOWN'),
((SELECT id FROM airports WHERE icao_code = 'KBLI'), 'SMALL_COMMERCIAL', TRUE, 'NORMAL', 0.00, 0.00, 'LOW', 'LOW', 'LOW', 'REGIONAL_JET', 'UNKNOWN'),
((SELECT id FROM airports WHERE icao_code = 'KAVL'), 'SMALL_COMMERCIAL', TRUE, 'NORMAL', 0.00, 0.00, 'LOW', 'LOW', 'LOW', 'REGIONAL_JET', 'UNKNOWN'),
((SELECT id FROM airports WHERE icao_code = 'CYKF'), 'SMALL_COMMERCIAL', TRUE, 'NORMAL', 0.00, 0.00, 'LOW', 'LOW', 'LOW', 'REGIONAL_JET', 'UNKNOWN'),
((SELECT id FROM airports WHERE icao_code = 'SBCT'), 'SMALL_COMMERCIAL', TRUE, 'NORMAL', 0.00, 0.00, 'LOW', 'LOW', 'LOW', 'NARROW_BODY', 'UNKNOWN'),
((SELECT id FROM airports WHERE icao_code = 'SAME'), 'SMALL_COMMERCIAL', TRUE, 'NORMAL', 0.00, 0.00, 'LOW', 'LOW', 'LOW', 'NARROW_BODY', 'UNKNOWN'),
((SELECT id FROM airports WHERE icao_code = 'FACT'), 'SMALL_COMMERCIAL', TRUE, 'EASY', 0.00, 0.00, 'LOW', 'LOW', 'LOW', 'NARROW_BODY', 'UNKNOWN'),
((SELECT id FROM airports WHERE icao_code = 'HKMO'), 'SMALL_COMMERCIAL', TRUE, 'NORMAL', 0.00, 0.00, 'LOW', 'LOW', 'LOW', 'REGIONAL_JET', 'UNKNOWN'),
((SELECT id FROM airports WHERE icao_code = 'YBCS'), 'SMALL_COMMERCIAL', TRUE, 'NORMAL', 0.00, 0.00, 'LOW', 'LOW', 'LOW', 'NARROW_BODY', 'UNKNOWN'),
((SELECT id FROM airports WHERE icao_code = 'RJBB'), 'SMALL_COMMERCIAL', TRUE, 'HARD', 0.00, 0.00, 'LOW', 'LOW', 'LOW', 'NARROW_BODY', 'UNKNOWN'),
((SELECT id FROM airports WHERE icao_code = 'VOCI'), 'SMALL_COMMERCIAL', TRUE, 'NORMAL', 0.00, 0.00, 'LOW', 'LOW', 'LOW', 'NARROW_BODY', 'UNKNOWN'),
((SELECT id FROM airports WHERE icao_code = 'AGGH'), 'SMALL_COMMERCIAL', TRUE, 'HARD', 0.00, 0.00, 'LOW', 'LOW', 'LOW', 'REGIONAL_JET', 'UNKNOWN')
ON DUPLICATE KEY UPDATE
  airport_size = VALUES(airport_size),
  starter_base_allowed = VALUES(starter_base_allowed),
  starter_difficulty = VALUES(starter_difficulty),
  base_opening_cost = VALUES(base_opening_cost),
  monthly_base_cost = VALUES(monthly_base_cost),
  slot_cost_level = VALUES(slot_cost_level),
  passenger_demand_level = VALUES(passenger_demand_level),
  cargo_demand_level = VALUES(cargo_demand_level),
  max_aircraft_class = VALUES(max_aircraft_class),
  runway_category = VALUES(runway_category);
