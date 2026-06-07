USE icaro_ops;

START TRANSACTION;

/*
 * Fix zero aircraft prices after full catalog import.
 *
 * The import is correct:
 * - 301 total models
 * - 292 from aircrafts.ods
 * - 9 pre-existing curated aircraft
 *
 * Some pre-existing aircraft had new_purchase_price = 0.00.
 * Since the Fleet market is sorted by price ASC, those aircraft appear first
 * as if they were free.
 *
 * This migration only fixes aircraft whose new_purchase_price is NULL or <= 0.
 * Existing valid prices are preserved.
 */

UPDATE aircraft_models
SET
  new_purchase_price = CASE
    WHEN icao_type_code = 'CONC' OR model_code = 'CONCORDE' THEN 250000000.00
    WHEN icao_type_code = 'E120' OR model_code = 'EMB120ER_BRASILIA' THEN 12000000.00
    WHEN icao_type_code = 'SF34' OR model_code = 'SAAB_340B' THEN 9000000.00
    WHEN base_purchase_price IS NOT NULL AND base_purchase_price > 0 THEN base_purchase_price
    WHEN aircraft_family = 'HELICOPTER' THEN GREATEST(900000.00, passenger_capacity_standard * 450000.00)
    WHEN aircraft_category = 'A' THEN GREATEST(180000.00, 120000.00 + passenger_capacity_standard * 140000.00)
    WHEN aircraft_category = 'B' THEN GREATEST(3000000.00, 2000000.00 + passenger_capacity_standard * 180000.00)
    WHEN aircraft_category = 'C' THEN GREATEST(18000000.00, 10000000.00 + passenger_capacity_standard * 240000.00)
    WHEN aircraft_category = 'D' THEN GREATEST(55000000.00, 28000000.00 + passenger_capacity_standard * 300000.00)
    WHEN aircraft_category = 'E' THEN GREATEST(120000000.00, 60000000.00 + passenger_capacity_standard * 450000.00)
    ELSE GREATEST(250000.00, passenger_capacity_standard * 150000.00)
  END
WHERE new_purchase_price IS NULL
   OR new_purchase_price <= 0;

UPDATE aircraft_models
SET base_purchase_price = new_purchase_price
WHERE base_purchase_price IS NULL
   OR base_purchase_price <= 0;

UPDATE aircraft_models
SET
  estimated_used_price_min = CASE
    WHEN estimated_used_price_min IS NULL OR estimated_used_price_min <= 0
    THEN ROUND(new_purchase_price * 0.35, 2)
    ELSE estimated_used_price_min
  END,
  estimated_used_price_max = CASE
    WHEN estimated_used_price_max IS NULL OR estimated_used_price_max <= 0
    THEN ROUND(new_purchase_price * 0.80, 2)
    ELSE estimated_used_price_max
  END,
  lease_price_per_day = CASE
    WHEN lease_price_per_day IS NULL OR lease_price_per_day <= 0
    THEN GREATEST(500.00, ROUND(new_purchase_price * 0.00045, 2))
    ELSE lease_price_per_day
  END
WHERE new_purchase_price > 0;

COMMIT;

SELECT
  model_code,
  icao_type_code,
  manufacturer,
  model_name,
  passenger_capacity_standard,
  new_purchase_price,
  base_purchase_price,
  estimated_used_price_min,
  estimated_used_price_max,
  lease_price_per_day
FROM aircraft_models
ORDER BY new_purchase_price ASC, model_code ASC
LIMIT 40;

SELECT COUNT(*) AS zero_or_missing_price_remaining
FROM aircraft_models
WHERE new_purchase_price IS NULL
   OR new_purchase_price <= 0;
