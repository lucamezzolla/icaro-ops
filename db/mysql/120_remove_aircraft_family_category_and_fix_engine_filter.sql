-- Icaro Ops
-- Normalize the aircraft market filter source of truth.
-- Engine filtering must use aircraft_models.engine_type only.
-- aircraft_family and aircraft_category are removed because they were inconsistent / overlapping.

START TRANSACTION;

UPDATE aircraft_models
SET engine_type = 'SUPERSONIC'
WHERE UPPER(COALESCE(model_name, '')) LIKE '%CONCORDE%'
   OR UPPER(COALESCE(model_code, '')) LIKE '%CONCORDE%'
   OR UPPER(COALESCE(model_code, '')) LIKE '%SSC_CONC%'
   OR UPPER(COALESCE(icao_type_code, '')) = 'CONC';

COMMIT;

DELIMITER //

DROP PROCEDURE IF EXISTS icaro_drop_aircraft_model_column_if_exists //

CREATE PROCEDURE icaro_drop_aircraft_model_column_if_exists(IN p_column_name VARCHAR(64))
BEGIN
  IF EXISTS (
    SELECT 1
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'aircraft_models'
      AND COLUMN_NAME = p_column_name
  ) THEN
    SET @ddl = CONCAT('ALTER TABLE aircraft_models DROP COLUMN ', p_column_name);
    PREPARE stmt FROM @ddl;
    EXECUTE stmt;
    DEALLOCATE PREPARE stmt;
  END IF;
END //

DELIMITER ;

CALL icaro_drop_aircraft_model_column_if_exists('aircraft_family');
CALL icaro_drop_aircraft_model_column_if_exists('aircraft_category');

DROP PROCEDURE IF EXISTS icaro_drop_aircraft_model_column_if_exists;
