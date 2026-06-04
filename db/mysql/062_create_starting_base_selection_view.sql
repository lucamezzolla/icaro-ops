-- Icaro Ops normalized starting base selection support.
--
-- This script creates only normalized rule/override tables and a calculated view.
-- It does NOT duplicate one gameplay profile row per airport.
--
-- Run:
--   sudo mysql icaro_ops < db/mysql/062_create_starting_base_selection_view.sql

USE icaro_ops;

START TRANSACTION;

CREATE TABLE IF NOT EXISTS airport_starting_base_blacklist (
  airport_icao_code CHAR(4) NOT NULL,
  reason VARCHAR(255) NOT NULL,
  created_at_utc TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

  PRIMARY KEY (airport_icao_code),

  CONSTRAINT fk_airport_starting_base_blacklist_airport
    FOREIGN KEY (airport_icao_code)
    REFERENCES airports(icao_code)
    ON UPDATE CASCADE
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS airport_starting_base_overrides (
  airport_icao_code CHAR(4) NOT NULL,

  force_eligible BOOLEAN NULL,
  base_tier_override VARCHAR(30) NULL,
  max_initial_aircraft_class_override VARCHAR(40) NULL,
  starting_base_score_override INT NULL,
  note VARCHAR(255) NULL,

  created_at_utc TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at_utc TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

  PRIMARY KEY (airport_icao_code),

  CONSTRAINT fk_airport_starting_base_overrides_airport
    FOREIGN KEY (airport_icao_code)
    REFERENCES airports(icao_code)
    ON UPDATE CASCADE
    ON DELETE CASCADE,

  CONSTRAINT chk_airport_starting_base_score_override
    CHECK (starting_base_score_override IS NULL OR (starting_base_score_override BETWEEN 0 AND 100))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS airport_market_overrides (
  airport_icao_code CHAR(4) NOT NULL,

  local_passenger_demand_score_override INT NULL,
  local_cargo_demand_score_override INT NULL,
  tourism_score_override INT NULL,
  business_score_override INT NULL,
  competition_score_override INT NULL,
  airport_fee_score_override INT NULL,
  starting_difficulty_override VARCHAR(20) NULL,
  note VARCHAR(255) NULL,

  created_at_utc TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at_utc TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

  PRIMARY KEY (airport_icao_code),

  CONSTRAINT fk_airport_market_overrides_airport
    FOREIGN KEY (airport_icao_code)
    REFERENCES airports(icao_code)
    ON UPDATE CASCADE
    ON DELETE CASCADE,

  CONSTRAINT chk_airport_market_passenger_score
    CHECK (local_passenger_demand_score_override IS NULL OR (local_passenger_demand_score_override BETWEEN 0 AND 100)),
  CONSTRAINT chk_airport_market_cargo_score
    CHECK (local_cargo_demand_score_override IS NULL OR (local_cargo_demand_score_override BETWEEN 0 AND 100)),
  CONSTRAINT chk_airport_market_tourism_score
    CHECK (tourism_score_override IS NULL OR (tourism_score_override BETWEEN 0 AND 100)),
  CONSTRAINT chk_airport_market_business_score
    CHECK (business_score_override IS NULL OR (business_score_override BETWEEN 0 AND 100)),
  CONSTRAINT chk_airport_market_competition_score
    CHECK (competition_score_override IS NULL OR (competition_score_override BETWEEN 0 AND 100)),
  CONSTRAINT chk_airport_market_fee_score
    CHECK (airport_fee_score_override IS NULL OR (airport_fee_score_override BETWEEN 0 AND 100))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Conservative manual hub blacklist for novice small-aircraft operations.
INSERT INTO airport_starting_base_blacklist (airport_icao_code, reason)
SELECT x.airport_icao_code, x.reason
FROM (
  SELECT 'LIRF' AS airport_icao_code, 'Large international hub; not suitable for novice small-aircraft operations.' AS reason
  UNION ALL SELECT 'OMDB', 'Large international hub; not suitable for novice small-aircraft operations.'
  UNION ALL SELECT 'KJFK', 'Large international hub; not suitable for novice small-aircraft operations.'
  UNION ALL SELECT 'KLAX', 'Large international hub; not suitable for novice small-aircraft operations.'
  UNION ALL SELECT 'KORD', 'Large international hub; not suitable for novice small-aircraft operations.'
  UNION ALL SELECT 'EGLL', 'Large international hub; not suitable for novice small-aircraft operations.'
  UNION ALL SELECT 'LFPG', 'Large international hub; not suitable for novice small-aircraft operations.'
  UNION ALL SELECT 'EDDF', 'Large international hub; not suitable for novice small-aircraft operations.'
  UNION ALL SELECT 'EHAM', 'Large international hub; not suitable for novice small-aircraft operations.'
  UNION ALL SELECT 'LEMD', 'Large international hub; not suitable for novice small-aircraft operations.'
  UNION ALL SELECT 'LTFM', 'Large international hub; not suitable for novice small-aircraft operations.'
  UNION ALL SELECT 'RJTT', 'Large international hub; not suitable for novice small-aircraft operations.'
  UNION ALL SELECT 'RJAA', 'Large international hub; not suitable for novice small-aircraft operations.'
  UNION ALL SELECT 'VHHH', 'Large international hub; not suitable for novice small-aircraft operations.'
  UNION ALL SELECT 'WSSS', 'Large international hub; not suitable for novice small-aircraft operations.'
  UNION ALL SELECT 'ZBAA', 'Large international hub; not suitable for novice small-aircraft operations.'
  UNION ALL SELECT 'ZSPD', 'Large international hub; not suitable for novice small-aircraft operations.'
  UNION ALL SELECT 'YSSY', 'Large international hub; not suitable for novice small-aircraft operations.'
) x
JOIN airports a
  ON a.icao_code = x.airport_icao_code
ON DUPLICATE KEY UPDATE
  reason = VALUES(reason);

CREATE OR REPLACE VIEW v_starting_base_airports AS
SELECT
  wr.code AS world_region_code,
  wr.name AS world_region_name,

  c.id AS country_id,
  c.name AS country_name,

  a.icao_code,
  a.iata_code,
  a.name AS airport_name,
  a.city,
  a.location_name,
  a.subdivision_name,
  a.latitude,
  a.longitude,
  a.airport_type,
  a.service_category,

  COALESCE(
    sbo.base_tier_override,
    CASE
      WHEN b.airport_icao_code IS NOT NULL THEN 'HUB'
      WHEN a.is_closed OR a.is_military OR NOT a.is_civilian THEN 'NOT_ELIGIBLE'
      WHEN a.airport_type = 'AIRSTRIP' THEN 'TOO_SMALL'
      WHEN a.service_category = 'INTERNATIONAL' THEN 'REGIONAL'
      WHEN a.airport_type = 'AIRFIELD' THEN 'SMALL'
      ELSE 'SMALL'
    END
  ) AS base_tier,

  COALESCE(
    sbo.max_initial_aircraft_class_override,
    CASE
      WHEN a.service_category = 'INTERNATIONAL' THEN 'TURBOPROP'
      ELSE 'LIGHT_COMMERCIAL'
    END
  ) AS max_initial_aircraft_class,

  COALESCE(
    sbo.starting_base_score_override,
    GREATEST(
      0,
      LEAST(
        100,
        40
        + CASE WHEN a.service_category = 'NATIONAL' THEN 25 ELSE 0 END
        + CASE WHEN a.service_category = 'INTERNATIONAL' THEN 5 ELSE 0 END
        + CASE WHEN a.iata_code IS NOT NULL THEN 5 ELSE 0 END
        + CASE WHEN a.latitude IS NOT NULL AND a.longitude IS NOT NULL THEN 10 ELSE 0 END
        + CASE WHEN a.airport_type = 'AIRFIELD' THEN -10 ELSE 0 END
        + CASE WHEN a.airport_type = 'AIRSTRIP' THEN -30 ELSE 0 END
        + CASE WHEN a.is_closed THEN -100 ELSE 0 END
        + CASE WHEN a.is_military THEN -100 ELSE 0 END
        + CASE WHEN NOT a.is_civilian THEN -100 ELSE 0 END
        + CASE WHEN b.airport_icao_code IS NOT NULL THEN -100 ELSE 0 END
      )
    )
  ) AS starting_base_score,

  COALESCE(
    amo.local_passenger_demand_score_override,
    GREATEST(0, LEAST(100,
      25
      + CASE WHEN a.service_category = 'NATIONAL' THEN 25 ELSE 0 END
      + CASE WHEN a.service_category = 'INTERNATIONAL' THEN 35 ELSE 0 END
      + CASE WHEN a.iata_code IS NOT NULL THEN 10 ELSE 0 END
    ))
  ) AS local_passenger_demand_score,

  COALESCE(
    amo.local_cargo_demand_score_override,
    GREATEST(0, LEAST(100,
      20
      + CASE WHEN a.service_category = 'NATIONAL' THEN 20 ELSE 0 END
      + CASE WHEN a.service_category = 'INTERNATIONAL' THEN 30 ELSE 0 END
      + CASE WHEN a.iata_code IS NOT NULL THEN 10 ELSE 0 END
    ))
  ) AS local_cargo_demand_score,

  COALESCE(
    amo.tourism_score_override,
    GREATEST(0, LEAST(100,
      20
      + CASE
          WHEN LOWER(a.name) LIKE '%island%' THEN 25
          WHEN LOWER(a.city) LIKE '%island%' THEN 20
          ELSE 0
        END
      + CASE WHEN a.service_category = 'INTERNATIONAL' THEN 20 ELSE 0 END
    ))
  ) AS tourism_score,

  COALESCE(
    amo.business_score_override,
    GREATEST(0, LEAST(100,
      20
      + CASE WHEN a.service_category = 'INTERNATIONAL' THEN 30 ELSE 0 END
      + CASE WHEN a.iata_code IS NOT NULL THEN 15 ELSE 0 END
    ))
  ) AS business_score,

  COALESCE(
    amo.competition_score_override,
    GREATEST(0, LEAST(100,
      20
      + CASE WHEN a.service_category = 'INTERNATIONAL' THEN 35 ELSE 0 END
      + CASE WHEN b.airport_icao_code IS NOT NULL THEN 40 ELSE 0 END
    ))
  ) AS competition_score,

  COALESCE(
    amo.airport_fee_score_override,
    GREATEST(0, LEAST(100,
      15
      + CASE WHEN a.service_category = 'NATIONAL' THEN 20 ELSE 0 END
      + CASE WHEN a.service_category = 'INTERNATIONAL' THEN 55 ELSE 0 END
      + CASE WHEN b.airport_icao_code IS NOT NULL THEN 25 ELSE 0 END
    ))
  ) AS airport_fee_score,

  COALESCE(
    amo.starting_difficulty_override,
    CASE
      WHEN b.airport_icao_code IS NOT NULL THEN 'LOCKED'
      WHEN a.is_closed OR a.is_military OR NOT a.is_civilian THEN 'LOCKED'
      WHEN a.latitude IS NULL OR a.longitude IS NULL THEN 'LOCKED'
      WHEN a.airport_type = 'AIRSTRIP' THEN 'LOCKED'
      WHEN a.service_category = 'INTERNATIONAL' THEN 'MEDIUM'
      ELSE 'EASY'
    END
  ) AS starting_difficulty,

  COALESCE(
    sbo.note,
    b.reason,
    CASE
      WHEN a.latitude IS NULL OR a.longitude IS NULL THEN 'Missing coordinates; excluded until reviewed.'
      WHEN a.service_category = 'INTERNATIONAL' THEN 'Regional/international airport; review cost and traffic before final balancing.'
      ELSE 'Calculated starting-base candidate.'
    END
  ) AS starting_base_note

FROM airports a
JOIN countries c
  ON c.id = a.country_id
JOIN world_regions wr
  ON wr.code = c.world_region_code
LEFT JOIN airport_starting_base_blacklist b
  ON b.airport_icao_code = a.icao_code
LEFT JOIN airport_starting_base_overrides sbo
  ON sbo.airport_icao_code = a.icao_code
LEFT JOIN airport_market_overrides amo
  ON amo.airport_icao_code = a.icao_code
WHERE
  COALESCE(
    sbo.force_eligible,
    CASE
      WHEN a.is_closed THEN FALSE
      WHEN a.is_military THEN FALSE
      WHEN NOT a.is_civilian THEN FALSE
      WHEN b.airport_icao_code IS NOT NULL THEN FALSE
      WHEN a.latitude IS NULL OR a.longitude IS NULL THEN FALSE
      WHEN a.airport_type NOT IN ('AIRPORT', 'AIRFIELD', 'AIRSTRIP') THEN FALSE
      WHEN a.airport_type = 'AIRSTRIP' THEN FALSE
      WHEN a.service_category = 'MILITARY' THEN FALSE
      WHEN (
        40
        + CASE WHEN a.service_category = 'NATIONAL' THEN 25 ELSE 0 END
        + CASE WHEN a.service_category = 'INTERNATIONAL' THEN 5 ELSE 0 END
        + CASE WHEN a.iata_code IS NOT NULL THEN 5 ELSE 0 END
        + CASE WHEN a.latitude IS NOT NULL AND a.longitude IS NOT NULL THEN 10 ELSE 0 END
        + CASE WHEN a.airport_type = 'AIRFIELD' THEN -10 ELSE 0 END
        + CASE WHEN a.service_category = 'INTERNATIONAL' THEN -15 ELSE 0 END
      ) >= 55 THEN TRUE
      ELSE FALSE
    END
  ) = TRUE
ORDER BY
  wr.name,
  c.name,
  starting_base_score DESC,
  a.name;

SELECT COUNT(*) AS starting_base_candidates
FROM v_starting_base_airports;

SELECT
  world_region_name,
  COUNT(*) AS starting_base_candidates
FROM v_starting_base_airports
GROUP BY world_region_name
ORDER BY world_region_name;

COMMIT;
