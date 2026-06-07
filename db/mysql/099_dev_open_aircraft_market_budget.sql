USE icaro_ops;

START TRANSACTION;

-- Development mode: make the test budget intentionally very high.
-- This is not gameplay balancing; it is only for development testing.
UPDATE companies
SET budget_amount = 500000000.00;

-- Optional normalization for the open market:
-- the new backend no longer needs these flags, but keeping them open helps
-- older UI/API paths that may still read them.
UPDATE aircraft_models
SET
  is_active = 1,
  is_available_new = 1,
  is_endgame = 0;

COMMIT;

SELECT
  id,
  company_name,
  budget_amount,
  currency_code
FROM companies
ORDER BY id;

SELECT
  COUNT(*) AS aircraft_models_visible_for_dev_market
FROM aircraft_models;
