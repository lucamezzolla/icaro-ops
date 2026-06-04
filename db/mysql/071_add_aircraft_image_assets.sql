-- Icaro Ops aircraft image assets.
--
-- Purpose:
--   Add local image paths to aircraft_models and refresh Fleet views so the UI
--   can show an Image button/dialog for every aircraft model in the current DB.
--
-- Run:
--   sudo mysql icaro_ops < db/mysql/071_add_aircraft_image_assets.sql

USE icaro_ops;

START TRANSACTION;

ALTER TABLE aircraft_models
  ADD COLUMN IF NOT EXISTS image_asset_path VARCHAR(255) NULL AFTER gameplay_notes;

UPDATE aircraft_models
SET image_asset_path = CASE model_code
  WHEN 'C208B_GRAND_CARAVAN_EX' THEN 'src/assets/aircraft/c208b_grand_caravan_ex.png'
  WHEN 'PC12_NGX' THEN 'src/assets/aircraft/pc12_ngx.png'
  WHEN 'B350_KING_AIR_360' THEN 'src/assets/aircraft/b350_king_air_360.png'
  WHEN 'DHC6_TWIN_OTTER_400' THEN 'src/assets/aircraft/dhc6_twin_otter_400.png'
  WHEN 'L410_NG' THEN 'src/assets/aircraft/l410_ng.png'
  WHEN 'SAAB_340B' THEN 'src/assets/aircraft/saab_340b.png'
  WHEN 'ATR42_600' THEN 'src/assets/aircraft/atr42_600.png'
  WHEN 'EMB120ER_BRASILIA' THEN 'src/assets/aircraft/emb120er_brasilia.png'
  WHEN 'CONCORDE' THEN 'src/assets/aircraft/concorde.png'
  ELSE image_asset_path
END
WHERE model_code IN (
  'C208B_GRAND_CARAVAN_EX',
  'PC12_NGX',
  'B350_KING_AIR_360',
  'DHC6_TWIN_OTTER_400',
  'L410_NG',
  'SAAB_340B',
  'ATR42_600',
  'EMB120ER_BRASILIA',
  'CONCORDE'
);

CREATE OR REPLACE VIEW v_company_fleet AS
SELECT
  ca.id AS company_aircraft_id,
  ca.company_id,
  co.company_name,

  ca.registration_code,
  ca.serial_number,
  ca.manufacture_year,
  ca.ownership_status,
  ca.acquisition_type,
  ca.purchase_price,
  ca.current_market_value,
  ca.currency_code,
  ca.home_base_icao_code,
  hb.name AS home_base_name,
  ca.current_airport_icao_code,
  ca_airport.name AS current_airport_name,
  ca.condition_percent,
  ca.airframe_hours,
  ca.cycles_count,
  ca.status,
  ca.is_available_for_sale,
  ca.asking_price,

  am.id AS aircraft_model_id,
  am.manufacturer,
  am.model_name,
  am.model_code,
  am.icao_type_code,
  am.iata_type_code,
  am.aircraft_family,
  am.aircraft_category,
  am.operation_role,
  am.engine_type,
  am.engine_count,
  am.crew_required_min,
  am.passenger_capacity_standard,
  am.passenger_capacity_max,
  am.cargo_capacity_kg,
  am.max_payload_kg,
  am.max_takeoff_weight_kg,
  am.cruise_speed_kmh,
  am.range_km,
  am.service_ceiling_ft,
  am.required_runway_m,
  am.fuel_burn_kg_per_hour,
  am.maintenance_cost_per_hour,
  am.new_purchase_price,
  am.estimated_used_price_min,
  am.estimated_used_price_max,
  am.lease_price_per_day,
  am.production_status,
  am.minimum_airport_size_tier,
  am.gameplay_notes,
  am.image_asset_path,

  ca.created_at_utc,
  ca.updated_at_utc

FROM company_aircraft ca
JOIN companies co
  ON co.id = ca.company_id
JOIN aircraft_models am
  ON am.id = ca.aircraft_model_id
JOIN airports hb
  ON hb.icao_code = ca.home_base_icao_code
JOIN airports ca_airport
  ON ca_airport.icao_code = ca.current_airport_icao_code;

CREATE OR REPLACE VIEW v_active_aircraft_catalog AS
SELECT
  am.id AS aircraft_model_id,
  am.manufacturer,
  am.model_name,
  am.model_code,
  am.icao_type_code,
  am.iata_type_code,
  am.aircraft_family,
  am.aircraft_category,
  am.operation_role,
  am.engine_type,
  am.engine_count,
  am.crew_required_min,
  am.passenger_capacity_standard,
  am.passenger_capacity_max,
  am.cargo_capacity_kg,
  am.max_payload_kg,
  am.max_takeoff_weight_kg,
  am.cruise_speed_kmh,
  am.range_km,
  am.service_ceiling_ft,
  am.required_runway_m,
  am.fuel_burn_kg_per_hour,
  am.maintenance_cost_per_hour,
  am.new_purchase_price,
  am.estimated_used_price_min,
  am.estimated_used_price_max,
  am.lease_price_per_day,
  am.currency_code,
  am.production_status,
  am.is_available_new,
  am.is_available_used,
  am.is_active,
  am.is_endgame,
  am.unlock_reputation_score,
  am.minimum_airport_size_tier,
  am.gameplay_notes,
  am.image_asset_path,
  am.data_quality
FROM aircraft_models am
WHERE am.is_active = TRUE;

CREATE OR REPLACE VIEW v_used_aircraft_market AS
SELECT
  v.company_aircraft_id,
  v.company_id AS seller_company_id,
  v.company_name AS seller_company_name,
  v.registration_code,
  v.manufacturer,
  v.model_name,
  v.model_code,
  v.icao_type_code,
  v.aircraft_category,
  v.operation_role,
  v.manufacture_year,
  v.condition_percent,
  v.airframe_hours,
  v.cycles_count,
  v.current_market_value,
  v.asking_price,
  v.currency_code,
  v.home_base_icao_code,
  v.current_airport_icao_code,
  v.current_airport_name,
  v.passenger_capacity_standard,
  v.cargo_capacity_kg,
  v.range_km,
  v.required_runway_m,
  v.image_asset_path,
  v.status
FROM v_company_fleet v
WHERE v.is_available_for_sale = TRUE
  AND v.ownership_status = 'OWNED'
  AND v.status IN ('PARKED', 'AVAILABLE', 'FOR_SALE');

SELECT model_code, image_asset_path
FROM aircraft_models
WHERE image_asset_path IS NOT NULL
ORDER BY model_code;

COMMIT;
