USE icaro_ops;

START TRANSACTION;

-- Development / test comfort budget.
-- The open aircraft market is now a gameplay rule; this budget boost is only for local testing.
UPDATE companies
SET budget_amount = 500000000.00;

-- Ensure every aircraft is visible in the market.
UPDATE aircraft_models
SET
  is_active = 1,
  is_available_new = 1,
  is_endgame = 0;

DROP TEMPORARY TABLE IF EXISTS tmp_world_staff_names;
CREATE TEMPORARY TABLE tmp_world_staff_names (
  seq INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  first_name VARCHAR(80) NOT NULL,
  last_name VARCHAR(80) NOT NULL,
  home_region_code VARCHAR(30) NOT NULL
);

INSERT INTO tmp_world_staff_names (first_name, last_name, home_region_code) VALUES
('Amina', 'Okafor', 'AFRICA'),
('Kwame', 'Mensah', 'AFRICA'),
('Thandiwe', 'Dlamini', 'AFRICA'),
('Nadia', 'El Amrani', 'AFRICA'),
('Hiroshi', 'Tanaka', 'ASIA'),
('Mei', 'Lin', 'ASIA'),
('Arjun', 'Nair', 'ASIA'),
('Sofia', 'Santos', 'SOUTH_AMERICA'),
('Mateo', 'Rojas', 'SOUTH_AMERICA'),
('Valentina', 'Silva', 'SOUTH_AMERICA'),
('Emily', 'Johnson', 'NORTH_AMERICA'),
('Noah', 'Williams', 'NORTH_AMERICA'),
('Grace', 'Miller', 'NORTH_AMERICA'),
('Oliver', 'Smith', 'EUROPE'),
('Amelia', 'Brown', 'EUROPE'),
('Lars', 'Johansen', 'EUROPE'),
('Anika', 'Schneider', 'EUROPE'),
('Marta', 'Kowalska', 'EUROPE'),
('Yuki', 'Sato', 'ASIA'),
('Fatima', 'Al Haddad', 'MIDDLE_EAST'),
('Omar', 'Demir', 'MIDDLE_EAST'),
('Leila', 'Khalil', 'MIDDLE_EAST'),
('Jack', 'Wilson', 'OCEANIA'),
('Isla', 'Taylor', 'OCEANIA');

-- Add one pilot candidate for every aircraft model in the DB.
INSERT INTO staff_candidates (
  first_name,
  last_name,
  display_name,
  staff_role,
  status,
  home_region_code,
  preferred_base_icao_code,
  age_years,
  experience_level,
  fear_score,
  courage_score,
  stress_tolerance_score,
  discipline_score,
  teamwork_score,
  reliability_score,
  ambition_score,
  fatigue_risk_score,
  flight_hours_total,
  aircraft_maintenance_hours_total,
  salary_per_flight,
  daily_retainer,
  revenue_share_percent,
  currency_code,
  hiring_bonus,
  morale_score,
  generated_at_utc,
  expires_at_utc
)
SELECT
  n.first_name,
  n.last_name,
  CONCAT(n.first_name, ' ', n.last_name),
  'PILOT',
  'AVAILABLE',
  n.home_region_code,
  NULL,
  25 + MOD(am.id, 30),
  CASE
    WHEN MOD(am.id, 3) = 0 THEN 'SENIOR'
    WHEN MOD(am.id, 3) = 1 THEN 'INTERMEDIATE'
    ELSE 'JUNIOR'
  END,
  5 + MOD(am.id, 20),
  65 + MOD(am.id, 30),
  60 + MOD(am.id, 35),
  60 + MOD(am.id, 35),
  55 + MOD(am.id, 40),
  60 + MOD(am.id, 35),
  50 + MOD(am.id, 45),
  10 + MOD(am.id, 35),
  250 + (am.id * 23),
  0,
  350.00 + (MOD(am.id, 12) * 40),
  80.00 + (MOD(am.id, 8) * 15),
  0.00,
  'EUR',
  500.00 + (MOD(am.id, 10) * 100),
  70,
  UTC_TIMESTAMP(),
  NULL
FROM aircraft_models am
JOIN tmp_world_staff_names n
  ON n.seq = 1 + MOD(am.id, (SELECT COUNT(*) FROM tmp_world_staff_names))
WHERE NOT EXISTS (
  SELECT 1
  FROM staff_candidates existing
  JOIN staff_candidate_licenses existing_license
    ON existing_license.candidate_id = existing.id
  WHERE existing.staff_role = 'PILOT'
    AND existing.status = 'AVAILABLE'
    AND existing_license.license_code = CASE
      WHEN am.model_code = 'C208B_GRAND_CARAVAN_EX' THEN 'C208_TYPE'
      WHEN am.model_code = 'DHC6_TWIN_OTTER_400' THEN 'DHC6_TYPE'
      WHEN am.model_code = 'ATR42_600' THEN 'ATR42_TYPE'
      WHEN am.icao_type_code IS NOT NULL AND am.icao_type_code <> '' THEN CONCAT(am.icao_type_code, '_TYPE')
      ELSE CONCAT(am.model_code, '_TYPE')
    END
);

-- Basic pilot licenses.
INSERT IGNORE INTO staff_candidate_licenses (candidate_id, license_code, proficiency_score, issued_at_utc, expires_at_utc)
SELECT id, 'CPL', 75, UTC_TIMESTAMP(), NULL
FROM staff_candidates
WHERE staff_role = 'PILOT';

INSERT IGNORE INTO staff_candidate_licenses (candidate_id, license_code, proficiency_score, issued_at_utc, expires_at_utc)
SELECT id, 'IR', 70, UTC_TIMESTAMP(), NULL
FROM staff_candidates
WHERE staff_role = 'PILOT';

-- Type rating candidates for every aircraft model.
INSERT IGNORE INTO staff_candidate_licenses (candidate_id, license_code, proficiency_score, issued_at_utc, expires_at_utc)
SELECT
  sc.id,
  CASE
    WHEN am.model_code = 'C208B_GRAND_CARAVAN_EX' THEN 'C208_TYPE'
    WHEN am.model_code = 'DHC6_TWIN_OTTER_400' THEN 'DHC6_TYPE'
    WHEN am.model_code = 'ATR42_600' THEN 'ATR42_TYPE'
    WHEN am.icao_type_code IS NOT NULL AND am.icao_type_code <> '' THEN CONCAT(am.icao_type_code, '_TYPE')
    ELSE CONCAT(am.model_code, '_TYPE')
  END,
  70 + MOD(am.id, 25),
  UTC_TIMESTAMP(),
  NULL
FROM aircraft_models am
JOIN staff_candidates sc
  ON sc.staff_role = 'PILOT'
 AND sc.status = 'AVAILABLE'
JOIN staff_candidate_licenses cpl
  ON cpl.candidate_id = sc.id
 AND cpl.license_code = 'CPL'
WHERE sc.id IN (
  SELECT MAX(sc2.id)
  FROM staff_candidates sc2
  GROUP BY sc2.display_name
);

-- Add worldwide technicians.
INSERT INTO staff_candidates (
  first_name,
  last_name,
  display_name,
  staff_role,
  status,
  home_region_code,
  preferred_base_icao_code,
  age_years,
  experience_level,
  fear_score,
  courage_score,
  stress_tolerance_score,
  discipline_score,
  teamwork_score,
  reliability_score,
  ambition_score,
  fatigue_risk_score,
  flight_hours_total,
  aircraft_maintenance_hours_total,
  salary_per_flight,
  daily_retainer,
  revenue_share_percent,
  currency_code,
  hiring_bonus,
  morale_score,
  generated_at_utc,
  expires_at_utc
)
SELECT
  n.first_name,
  n.last_name,
  CONCAT(n.first_name, ' ', n.last_name),
  'TECHNICIAN',
  'AVAILABLE',
  n.home_region_code,
  NULL,
  24 + MOD(n.seq, 32),
  CASE
    WHEN MOD(n.seq, 3) = 0 THEN 'SENIOR'
    WHEN MOD(n.seq, 3) = 1 THEN 'INTERMEDIATE'
    ELSE 'JUNIOR'
  END,
  5 + MOD(n.seq, 20),
  55 + MOD(n.seq, 35),
  65 + MOD(n.seq, 30),
  65 + MOD(n.seq, 30),
  60 + MOD(n.seq, 35),
  65 + MOD(n.seq, 30),
  45 + MOD(n.seq, 40),
  10 + MOD(n.seq, 35),
  0,
  400 + (n.seq * 45),
  0.00,
  120.00 + (MOD(n.seq, 10) * 20),
  0.00,
  'EUR',
  300.00 + (MOD(n.seq, 8) * 80),
  70,
  UTC_TIMESTAMP(),
  NULL
FROM tmp_world_staff_names n
WHERE NOT EXISTS (
  SELECT 1
  FROM staff_candidates existing
  WHERE existing.staff_role = 'TECHNICIAN'
    AND existing.display_name = CONCAT(n.first_name, ' ', n.last_name)
);

INSERT IGNORE INTO staff_candidate_licenses (candidate_id, license_code, proficiency_score, issued_at_utc, expires_at_utc)
SELECT id, 'A_AND_P', 75, UTC_TIMESTAMP(), NULL
FROM staff_candidates
WHERE staff_role = 'TECHNICIAN';

INSERT IGNORE INTO staff_candidate_licenses (candidate_id, license_code, proficiency_score, issued_at_utc, expires_at_utc)
SELECT id, 'GENERAL_MAINT', 75, UTC_TIMESTAMP(), NULL
FROM staff_candidates
WHERE staff_role = 'TECHNICIAN';

COMMIT;

SELECT id, company_name, budget_amount, currency_code
FROM companies
ORDER BY id;

SELECT staff_role, COUNT(*) AS available_candidates
FROM staff_candidates
WHERE status = 'AVAILABLE'
GROUP BY staff_role;
