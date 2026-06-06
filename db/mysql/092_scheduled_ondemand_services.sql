USE icaro_ops;

START TRANSACTION;

ALTER TABLE scheduled_services
  ADD COLUMN IF NOT EXISTS service_type VARCHAR(30) NOT NULL DEFAULT 'SCHEDULED'
  AFTER service_code;

ALTER TABLE scheduled_services
  MODIFY COLUMN scheduled_departure_time_utc TIME NULL;

ALTER TABLE scheduled_services
  ADD COLUMN IF NOT EXISTS compatible_aircraft_model_codes VARCHAR(500) NULL
  AFTER preferred_aircraft_model_id;

UPDATE scheduled_services
SET service_type = CASE
  WHEN scheduled_departure_time_utc IS NULL THEN 'ON_DEMAND'
  ELSE 'SCHEDULED'
END
WHERE service_type IS NULL
   OR service_type = '';

UPDATE scheduled_services
SET compatible_aircraft_model_codes = 'C208B_GRAND_CARAVAN_EX,PC12_NGX,DHC6_TWIN_OTTER_400,L410_NG'
WHERE compatible_aircraft_model_codes IS NULL
   OR compatible_aircraft_model_codes = '';

COMMIT;

SELECT 'Scheduled/on-demand service fields installed' AS result;
