-- Icaro Ops airport capacity, occupied base slots and slot offers.
--
-- Purpose:
--   Apply a base-capacity rule to every airport and expose slot availability.
--
-- Requires:
--   airports
--   companies
--   rival_companies
--   rival_company_bases
--   airport_capacity_profiles
--
-- Run:
--   sudo mysql icaro_ops < db/mysql/066_airport_capacity_slots_and_offers.sql

USE icaro_ops;

START TRANSACTION;

CREATE TABLE IF NOT EXISTS airport_base_slot_offers (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,

  airport_icao_code CHAR(4) NOT NULL,

  requester_type VARCHAR(20) NOT NULL DEFAULT 'PLAYER',
  requester_company_id BIGINT UNSIGNED NULL,
  requester_rival_company_id BIGINT UNSIGNED NULL,

  offered_amount DECIMAL(15,2) NOT NULL,
  currency_code CHAR(3) NOT NULL DEFAULT 'EUR',

  status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
  decision_note VARCHAR(255) NULL,

  created_at_utc TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  decided_at_utc TIMESTAMP NULL,

  PRIMARY KEY (id),

  KEY idx_airport_base_slot_offers_airport_status (airport_icao_code, status),
  KEY idx_airport_base_slot_offers_requester_company (requester_company_id),
  KEY idx_airport_base_slot_offers_requester_rival (requester_rival_company_id),

  CONSTRAINT fk_airport_base_slot_offers_airport
    FOREIGN KEY (airport_icao_code)
    REFERENCES airports(icao_code)
    ON UPDATE CASCADE
    ON DELETE CASCADE,

  CONSTRAINT fk_airport_base_slot_offers_company
    FOREIGN KEY (requester_company_id)
    REFERENCES companies(id)
    ON UPDATE CASCADE
    ON DELETE CASCADE,

  CONSTRAINT fk_airport_base_slot_offers_rival_company
    FOREIGN KEY (requester_rival_company_id)
    REFERENCES rival_companies(id)
    ON UPDATE CASCADE
    ON DELETE CASCADE,

  CONSTRAINT chk_airport_base_slot_offers_amount
    CHECK (offered_amount > 0),

  CONSTRAINT chk_airport_base_slot_offers_currency
    CHECK (currency_code IN ('EUR', 'USD')),

  CONSTRAINT chk_airport_base_slot_offers_requester_type
    CHECK (requester_type IN ('PLAYER', 'RIVAL')),

  CONSTRAINT chk_airport_base_slot_offers_status
    CHECK (status IN ('PENDING', 'ACCEPTED', 'REJECTED', 'EXPIRED', 'CANCELLED'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Ensure every airport has a capacity profile.
-- This is a first deterministic gameplay rule; it can be refined per airport later.
INSERT INTO airport_capacity_profiles (
  airport_icao_code,
  airport_size_tier,
  max_player_bases,
  max_rival_bases,
  max_total_bases,
  note
)
SELECT
  a.icao_code,

  CASE
    WHEN a.is_closed THEN 'CLOSED'
    WHEN a.is_military OR NOT a.is_civilian THEN 'RESTRICTED'
    WHEN a.airport_type = 'AIRSTRIP' THEN 'AIRSTRIP'
    WHEN a.service_category = 'INTERNATIONAL' AND a.iata_code IS NOT NULL THEN 'REGIONAL'
    WHEN a.service_category = 'INTERNATIONAL' THEN 'REGIONAL'
    WHEN a.service_category = 'NATIONAL' THEN 'MEDIUM'
    WHEN a.airport_type = 'AIRFIELD' THEN 'SMALL'
    ELSE 'SMALL'
  END AS airport_size_tier,

  CASE
    WHEN a.is_closed THEN 0
    WHEN a.is_military OR NOT a.is_civilian THEN 0
    WHEN a.airport_type = 'AIRSTRIP' THEN 1
    WHEN a.service_category = 'INTERNATIONAL' THEN 2
    WHEN a.service_category = 'NATIONAL' THEN 1
    ELSE 1
  END AS max_player_bases,

  CASE
    WHEN a.is_closed THEN 0
    WHEN a.is_military OR NOT a.is_civilian THEN 0
    WHEN a.airport_type = 'AIRSTRIP' THEN 0
    WHEN a.service_category = 'INTERNATIONAL' THEN 3
    WHEN a.service_category = 'NATIONAL' THEN 1
    ELSE 0
  END AS max_rival_bases,

  CASE
    WHEN a.is_closed THEN 0
    WHEN a.is_military OR NOT a.is_civilian THEN 0
    WHEN a.airport_type = 'AIRSTRIP' THEN 1
    WHEN a.service_category = 'INTERNATIONAL' THEN 5
    WHEN a.service_category = 'NATIONAL' THEN 2
    ELSE 1
  END AS max_total_bases,

  'Initial global airport capacity rule. Review and override per airport over time.'
FROM airports a
ON DUPLICATE KEY UPDATE
  -- Preserve manual reviewed airport_size_tier and max values.
  note = CASE
    WHEN airport_capacity_profiles.note LIKE 'Rome Ciampino:%' THEN airport_capacity_profiles.note
    ELSE VALUES(note)
  END;

-- Manual reviewed override: LIRA / Rome Ciampino.
INSERT INTO airport_capacity_profiles (
  airport_icao_code,
  airport_size_tier,
  max_player_bases,
  max_rival_bases,
  max_total_bases,
  note
)
SELECT
  'LIRA',
  'MEDIUM',
  1,
  1,
  2,
  'Rome Ciampino: medium starting airport, max 2 total bases for early-game balancing.'
FROM airports
WHERE icao_code = 'LIRA'
ON DUPLICATE KEY UPDATE
  airport_size_tier = VALUES(airport_size_tier),
  max_player_bases = VALUES(max_player_bases),
  max_rival_bases = VALUES(max_rival_bases),
  max_total_bases = VALUES(max_total_bases),
  note = VALUES(note);

CREATE OR REPLACE VIEW v_airport_base_occupants AS
SELECT
  'PLAYER' AS occupant_type,
  co.id AS occupant_company_id,
  NULL AS occupant_rival_company_id,
  co.company_name,
  co.base_airport_icao_code AS airport_icao_code,
  co.created_at_utc
FROM companies co

UNION ALL

SELECT
  'RIVAL' AS occupant_type,
  NULL AS occupant_company_id,
  rc.id AS occupant_rival_company_id,
  rc.company_name,
  rb.airport_icao_code,
  rb.created_at_utc
FROM rival_company_bases rb
JOIN rival_companies rc
  ON rc.id = rb.rival_company_id
WHERE rc.is_active = TRUE;

CREATE OR REPLACE VIEW v_airport_base_capacity_status AS
SELECT
  a.icao_code AS airport_icao_code,
  a.iata_code,
  a.name AS airport_name,
  a.city,
  c.name AS country_name,
  wr.code AS world_region_code,
  wr.name AS world_region_name,

  acp.airport_size_tier,
  acp.max_player_bases,
  acp.max_rival_bases,
  acp.max_total_bases,

  COALESCE(SUM(CASE WHEN o.occupant_type = 'PLAYER' THEN 1 ELSE 0 END), 0) AS used_player_bases,
  COALESCE(SUM(CASE WHEN o.occupant_type = 'RIVAL' THEN 1 ELSE 0 END), 0) AS used_rival_bases,
  COALESCE(COUNT(o.airport_icao_code), 0) AS used_total_bases,

  GREATEST(acp.max_player_bases - COALESCE(SUM(CASE WHEN o.occupant_type = 'PLAYER' THEN 1 ELSE 0 END), 0), 0) AS available_player_base_slots,
  GREATEST(acp.max_rival_bases - COALESCE(SUM(CASE WHEN o.occupant_type = 'RIVAL' THEN 1 ELSE 0 END), 0), 0) AS available_rival_base_slots,
  GREATEST(acp.max_total_bases - COALESCE(COUNT(o.airport_icao_code), 0), 0) AS available_total_base_slots,

  CASE
    WHEN acp.max_total_bases <= COALESCE(COUNT(o.airport_icao_code), 0) THEN TRUE
    ELSE FALSE
  END AS is_full,

  acp.note
FROM airports a
JOIN countries c
  ON c.id = a.country_id
JOIN world_regions wr
  ON wr.code = c.world_region_code
JOIN airport_capacity_profiles acp
  ON acp.airport_icao_code = a.icao_code
LEFT JOIN v_airport_base_occupants o
  ON o.airport_icao_code = a.icao_code
GROUP BY
  a.icao_code,
  a.iata_code,
  a.name,
  a.city,
  c.name,
  wr.code,
  wr.name,
  acp.airport_size_tier,
  acp.max_player_bases,
  acp.max_rival_bases,
  acp.max_total_bases,
  acp.note;

SELECT
  airport_icao_code,
  airport_name,
  airport_size_tier,
  max_total_bases,
  used_total_bases,
  available_total_base_slots,
  is_full
FROM v_airport_base_capacity_status
WHERE airport_icao_code = 'LIRA';

COMMIT;
