USE icaro_ops;

START TRANSACTION;

-- Ensure ICAO aircraft type designators are available for the current catalog.
-- These are aircraft type codes, not airport ICAO codes.
UPDATE aircraft_models
SET icao_type_code = 'C208'
WHERE model_code = 'C208B_GRAND_CARAVAN_EX';

UPDATE aircraft_models
SET icao_type_code = 'PC12'
WHERE model_code = 'PC12_NGX';

UPDATE aircraft_models
SET icao_type_code = 'DHC6'
WHERE model_code = 'DHC6_TWIN_OTTER_400';

UPDATE aircraft_models
SET icao_type_code = 'L410'
WHERE model_code = 'L410_NG';

UPDATE aircraft_models
SET icao_type_code = 'AT46'
WHERE model_code = 'ATR42_600';

UPDATE aircraft_models
SET icao_type_code = 'BE30'
WHERE model_code = 'B350_KING_AIR_360';

UPDATE aircraft_models
SET icao_type_code = 'CONC'
WHERE model_code = 'CONCORDE';

UPDATE aircraft_models
SET icao_type_code = 'E120'
WHERE model_code = 'EMB120ER_BRASILIA';

UPDATE aircraft_models
SET icao_type_code = 'SF34'
WHERE model_code = 'SAAB_340B';

-- Store compatible models internally as model_code, but expose ICAO codes from API/UI.
UPDATE scheduled_services
SET compatible_aircraft_model_codes = 'C208B_GRAND_CARAVAN_EX,PC12_NGX,DHC6_TWIN_OTTER_400,L410_NG'
WHERE compatible_aircraft_model_codes IS NULL
   OR compatible_aircraft_model_codes = ''
   OR compatible_aircraft_model_codes LIKE '%C208B_GRAND_CARAVAN_EX%';

COMMIT;

SELECT
  model_code,
  icao_type_code,
  manufacturer,
  model_name
FROM aircraft_models
WHERE model_code IN (
  'C208B_GRAND_CARAVAN_EX',
  'PC12_NGX',
  'DHC6_TWIN_OTTER_400',
  'L410_NG',
  'ATR42_600',
  'B350_KING_AIR_360',
  'CONCORDE',
  'EMB120ER_BRASILIA',
  'SAAB_340B'
)
ORDER BY model_code;
