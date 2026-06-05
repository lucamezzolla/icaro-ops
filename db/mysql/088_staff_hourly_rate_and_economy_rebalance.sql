USE icaro_ops;

START TRANSACTION;

ALTER TABLE staff_candidates
  ADD COLUMN IF NOT EXISTS hourly_rate DECIMAL(12,2) NOT NULL DEFAULT 0.00
  AFTER daily_retainer;

ALTER TABLE company_staff
  ADD COLUMN IF NOT EXISTS hourly_rate DECIMAL(12,2) NOT NULL DEFAULT 0.00
  AFTER daily_retainer;

-- Rebalance existing pilots.
-- salary_per_flight is now interpreted as fixed leg fee, not full flight salary.
UPDATE company_staff
SET
  salary_per_flight = CASE
    WHEN staff_role = 'PILOT' THEN 55.00 + (id % 4) * 10.00
    ELSE salary_per_flight
  END,
  hourly_rate = CASE
    WHEN staff_role = 'PILOT' THEN 85.00 + (id % 5) * 12.00
    ELSE hourly_rate
  END
WHERE staff_role = 'PILOT';

-- Technicians are not normal flight crew cost.
-- Their hourly rate is for maintenance work.
UPDATE company_staff
SET
  salary_per_flight = 0.00,
  hourly_rate = 45.00 + (id % 5) * 8.00
WHERE staff_role = 'TECHNICIAN';

-- Rebalance available candidates.
UPDATE staff_candidates
SET
  salary_per_flight = CASE
    WHEN staff_role = 'PILOT' THEN 55.00 + (id % 5) * 10.00
    ELSE 0.00
  END,
  hourly_rate = CASE
    WHEN staff_role = 'PILOT' THEN 80.00 + (id % 6) * 12.00
    WHEN staff_role = 'TECHNICIAN' THEN 45.00 + (id % 6) * 8.00
    ELSE hourly_rate
  END
WHERE status = 'AVAILABLE';

SELECT
  id,
  display_name,
  staff_role,
  salary_per_flight AS leg_fee,
  hourly_rate,
  daily_retainer,
  revenue_share_percent,
  currency_code
FROM company_staff
ORDER BY staff_role, display_name;

COMMIT;
