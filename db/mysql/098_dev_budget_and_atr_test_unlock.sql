USE icaro_ops;

START TRANSACTION;

-- Development-only test boost.
-- Adjust company_id if you reset and your company gets a different id.
UPDATE companies
SET budget_amount = budget_amount + 20000000.00
WHERE id = 1;

-- Make sure ATR is buyable for this development test.
UPDATE aircraft_models
SET
  is_active = 1,
  is_available_new = 1,
  is_endgame = 0,
  icao_type_code = 'AT46'
WHERE model_code = 'ATR42_600';

-- For the current purchase rule, buying the second aircraft requires 4 pilots
-- qualified for the target aircraft type. Grant ATR42_TYPE to up to 4 active pilots.
INSERT IGNORE INTO company_staff_licenses (
  company_staff_id,
  license_code,
  proficiency_score,
  issued_at_utc,
  expires_at_utc
)
SELECT
  s.id,
  'ATR42_TYPE',
  70,
  UTC_TIMESTAMP(),
  NULL
FROM company_staff s
WHERE s.company_id = 1
  AND s.staff_role = 'PILOT'
  AND s.employment_status = 'ACTIVE'
ORDER BY
  s.reliability_score DESC,
  s.id
LIMIT 4;

COMMIT;

SELECT
  id,
  company_name,
  budget_amount
FROM companies
WHERE id = 1;

SELECT
  am.model_code,
  am.icao_type_code,
  am.manufacturer,
  am.model_name,
  am.new_purchase_price,
  am.is_active,
  am.is_available_new,
  am.is_endgame
FROM aircraft_models am
WHERE am.model_code = 'ATR42_600';

SELECT
  s.id,
  s.display_name,
  GROUP_CONCAT(l.license_code ORDER BY l.license_code SEPARATOR ', ') AS licenses
FROM company_staff s
LEFT JOIN company_staff_licenses l
  ON l.company_staff_id = s.id
WHERE s.company_id = 1
  AND s.staff_role = 'PILOT'
GROUP BY
  s.id,
  s.display_name
ORDER BY
  s.id;
