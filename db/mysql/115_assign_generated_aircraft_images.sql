USE icaro_ops;

START TRANSACTION;

/*
 * Assign generated aircraft images to models that do not already have one.
 * Existing image_asset_path values are preserved.
 */

UPDATE aircraft_models
SET image_asset_path = CASE
  WHEN icao_type_code = 'CONC'
    OR model_code = 'CONCORDE'
    OR LOWER(model_name) LIKE '%concorde%'
  THEN 'src/img/aircraft/generated/concorde.svg'

  WHEN aircraft_family = 'HELICOPTER'
  THEN 'src/img/aircraft/generated/helicopter.svg'

  WHEN engine_type = 'JET'
  THEN 'src/img/aircraft/generated/jet.svg'

  WHEN engine_type = 'TURBOPROP'
  THEN 'src/img/aircraft/generated/turboprop.svg'

  ELSE 'src/img/aircraft/generated/fixed-wing.svg'
END
WHERE image_asset_path IS NULL
   OR image_asset_path = '';

COMMIT;

SELECT
  image_asset_path,
  COUNT(*) AS aircraft_count
FROM aircraft_models
GROUP BY image_asset_path
ORDER BY aircraft_count DESC, image_asset_path;
