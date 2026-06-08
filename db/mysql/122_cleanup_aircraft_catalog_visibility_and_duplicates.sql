-- Icaro Ops
-- 122_cleanup_aircraft_catalog_visibility_and_duplicates.sql
--
-- Purpose:
--   Clean the aircraft purchase catalog without deleting historical rows.
--   Non-commercial / non-airline aircraft and obvious duplicate catalog rows are hidden
--   with is_active = 0, so the data can still be reviewed later.
--
-- Notes:
--   - Prices are intentionally NOT mass-updated here.
--   - This migration assumes db/mysql/120 already normalized engine_type.
--   - If 120 has not been applied, this migration still works because it only depends
--     on stable columns: id, manufacturer, model_name, is_active.

START TRANSACTION;

-- -----------------------------------------------------------------------------
-- 1) Keep the best/most believable duplicate rows visible.
-- -----------------------------------------------------------------------------

-- Concorde: keep id 9 because it is the curated retired Concorde row.
UPDATE aircraft_models
SET manufacturer = 'Aérospatiale/BAC',
    model_name = 'Concorde',
    engine_type = 'SUPERSONIC',
    production_status = 'RETIRED',
    is_active = 1
WHERE id = 9;

-- Cessna Caravan: keep the curated/in-production 208B Grand Caravan EX row.
UPDATE aircraft_models
SET manufacturer = 'Textron Aviation / Cessna',
    model_name = '208B Grand Caravan EX',
    engine_type = 'TURBOPROP',
    production_status = 'IN_PRODUCTION',
    is_active = 1
WHERE id = 1;

-- DHC-6: keep the in-production Series 400 row.
UPDATE aircraft_models
SET manufacturer = 'De Havilland Canada',
    model_name = 'DHC-6 Twin Otter Series 400',
    engine_type = 'TURBOPROP',
    production_status = 'IN_PRODUCTION',
    is_active = 1
WHERE id = 4;

-- PC-12: keep the NGX row; it has the more believable modern aircraft data.
UPDATE aircraft_models
SET manufacturer = 'Pilatus Aircraft',
    model_name = 'PC-12 NGX',
    engine_type = 'TURBOPROP',
    production_status = 'IN_PRODUCTION',
    is_active = 1
WHERE id = 2;

-- Saab 340: keep the curated 340B row.
UPDATE aircraft_models
SET manufacturer = 'Saab',
    model_name = '340B',
    engine_type = 'TURBOPROP',
    production_status = 'OUT_OF_PRODUCTION',
    is_active = 1
WHERE id = 6;

-- EMB 120: keep the curated ER Brasilia row.
UPDATE aircraft_models
SET manufacturer = 'Embraer',
    model_name = 'EMB 120ER Brasília',
    engine_type = 'TURBOPROP',
    production_status = 'OUT_OF_PRODUCTION',
    is_active = 1
WHERE id = 8;

-- Beechcraft 1900: keep 1900D; hide the generic 1900/1900C/1900D row below.
UPDATE aircraft_models
SET manufacturer = 'Beechcraft',
    model_name = '1900D',
    engine_type = 'TURBOPROP',
    is_active = 1
WHERE id = 121;

-- King Air: keep the specific King Air 350i row; hide the generic B350 row below.
UPDATE aircraft_models
SET manufacturer = 'Beechcraft',
    model_name = 'King Air 350i',
    engine_type = 'TURBOPROP',
    is_active = 1
WHERE id = 118;

-- -----------------------------------------------------------------------------
-- 2) Hide obvious duplicates, generic rows, or rows with less believable values.
-- -----------------------------------------------------------------------------
UPDATE aircraft_models
SET is_active = 0
WHERE id IN (
  285, -- duplicate Concorde imported from aircrafts.ods; keep id 9
  146, -- duplicate C208 with less believable piston/price data; keep id 1
  153, -- duplicate C208 generic row; keep id 1
  193, -- duplicate DHC-6 generic row; keep id 4
  256, -- duplicate PC-12 with less believable piston/price data; keep id 2
  281, -- duplicate Saab SF340A/B; keep id 6
  207, -- duplicate/generic Embraer 120; keep id 8
  115, -- generic Beechcraft 1900/1900C/1900D; keep id 121
  123, -- generic King Air 350 row; keep id 118
  188  -- unclear Falcon M row sharing FA50 code; keep Falcon 50 id 186
);

-- -----------------------------------------------------------------------------
-- 3) Hide aircraft that do not fit the main airline/business operations catalog.
--    They are not deleted: future game modes may reuse them for flight school,
--    air shows, museums, private ownership, or special events.
-- -----------------------------------------------------------------------------
UPDATE aircraft_models
SET is_active = 0
WHERE id IN (
  198, -- Extra 300/330/350 aerobatic aircraft
  273, -- Aviat Pitts Special S2S aerobatic aircraft
  125, -- Bellanca Scout / Super Decathlon aerobatic/training aircraft
  299, -- XtremeAir XA-42 Sbach 342 aerobatic aircraft
  86,  -- ICON A5 recreational light sport aircraft
  194, -- Austflight Drifter ultralight
  163, -- Flight Design CTSL light sport aircraft
  195, -- Diamond DV20 / DA20 trainer-like row
  177, -- DA20 Katana trainer-like row
  217, -- Kitfox STi FreedomFox / Fox2 kit/recreational aircraft
  237, -- Lancair Legacy experimental/recreational aircraft
  271, -- Pipistrel Virus SW 121 light sport aircraft
  286, -- ICP Savannah ultralight/light sport aircraft
  296, -- JMB Aircraft VL-3 ultralight/light sport aircraft
  284, -- Sting S4 ultralight
  282, -- Tecnam P-2002 Sierra light/training aircraft
  128, -- Tecnam P-2004 Bravo light/training aircraft
  262, -- Tecnam P92 light/training aircraft
  275, -- Van's RV-14/14A kit/recreational aircraft
  279, -- Zlin Savage Cub / Shock Ultra recreational aircraft
  141, -- Zenith STOL CH801 kit/recreational aircraft
  297, -- Waco vintage aircraft
  280, -- Schweizer 2-32 glider
  251, -- Hawker Hurricane warbird
  260, -- P-51D Mustang warbird
  298, -- Vought F4U Corsair warbird
  252, -- De Havilland Mosquito warbird
  212, -- SIAI-Marchetti SF-260 military/trainer special case
  133  -- Caproni Vizzola C-22J special/military trainer case
);

-- -----------------------------------------------------------------------------
-- 4) Professional naming cleanup for rows affected by this catalog cleanup.
--    Hidden rows are still renamed to keep the DB understandable.
-- -----------------------------------------------------------------------------
UPDATE aircraft_models SET manufacturer = 'Extra Aircraft', model_name = 'EA-300 / EA-330 / EA-350 aerobatic series' WHERE id = 198;
UPDATE aircraft_models SET manufacturer = 'Aviat Aircraft', model_name = 'Pitts Special S-2S' WHERE id = 273;
UPDATE aircraft_models SET manufacturer = 'American Champion', model_name = 'Scout / Super Decathlon' WHERE id = 125;
UPDATE aircraft_models SET manufacturer = 'XtremeAir', model_name = 'XA-42 Sbach 342' WHERE id = 299;
UPDATE aircraft_models SET manufacturer = 'ICON Aircraft', model_name = 'A5' WHERE id = 86;
UPDATE aircraft_models SET manufacturer = 'Austflight', model_name = 'Drifter' WHERE id = 194;
UPDATE aircraft_models SET manufacturer = 'Flight Design', model_name = 'CTSL' WHERE id = 163;
UPDATE aircraft_models SET manufacturer = 'Diamond Aircraft', model_name = 'DA20 Katana' WHERE id IN (177, 195);
UPDATE aircraft_models SET manufacturer = 'Kitfox Aircraft', model_name = 'STi FreedomFox / Fox2' WHERE id = 217;
UPDATE aircraft_models SET manufacturer = 'Lancair', model_name = 'Legacy' WHERE id = 237;
UPDATE aircraft_models SET manufacturer = 'Pipistrel', model_name = 'Virus SW 121' WHERE id = 271;
UPDATE aircraft_models SET manufacturer = 'ICP', model_name = 'Savannah' WHERE id = 286;
UPDATE aircraft_models SET manufacturer = 'JMB Aircraft', model_name = 'VL-3' WHERE id = 296;
UPDATE aircraft_models SET manufacturer = 'TL-Ultralight', model_name = 'Sting S4' WHERE id = 284;
UPDATE aircraft_models SET manufacturer = 'Tecnam', model_name = 'P2002 Sierra' WHERE id = 282;
UPDATE aircraft_models SET manufacturer = 'Tecnam', model_name = 'P2004 Bravo' WHERE id = 128;
UPDATE aircraft_models SET manufacturer = 'Tecnam', model_name = 'P92' WHERE id = 262;
UPDATE aircraft_models SET manufacturer = 'Van''s Aircraft', model_name = 'RV-14 / RV-14A' WHERE id = 275;
UPDATE aircraft_models SET manufacturer = 'Zlin Aviation', model_name = 'Savage Cub / Shock Ultra' WHERE id = 279;
UPDATE aircraft_models SET manufacturer = 'Zenith Aircraft', model_name = 'STOL CH 801' WHERE id = 141;
UPDATE aircraft_models SET manufacturer = 'Waco Aircraft', model_name = 'Vintage 1929' WHERE id = 297;
UPDATE aircraft_models SET manufacturer = 'Schweizer', model_name = '2-32' WHERE id = 280;
UPDATE aircraft_models SET manufacturer = 'Hawker', model_name = 'Hurricane Mk I' WHERE id = 251;
UPDATE aircraft_models SET manufacturer = 'North American Aviation', model_name = 'P-51D Mustang' WHERE id = 260;
UPDATE aircraft_models SET manufacturer = 'Vought', model_name = 'F4U Corsair' WHERE id = 298;
UPDATE aircraft_models SET manufacturer = 'De Havilland', model_name = 'Mosquito' WHERE id = 252;
UPDATE aircraft_models SET manufacturer = 'SIAI-Marchetti', model_name = 'SF-260' WHERE id = 212;
UPDATE aircraft_models SET manufacturer = 'Caproni Vizzola', model_name = 'C-22J Ventura' WHERE id = 133;

-- Correct a few duplicate/generic names even though the rows are now hidden.
UPDATE aircraft_models SET manufacturer = 'Aérospatiale/BAC', model_name = 'Concorde' WHERE id = 285;
UPDATE aircraft_models SET manufacturer = 'Cessna', model_name = '208B Grand Caravan EX' WHERE id = 146;
UPDATE aircraft_models SET manufacturer = 'Cessna', model_name = '208 Caravan' WHERE id = 153;
UPDATE aircraft_models SET manufacturer = 'De Havilland Canada', model_name = 'DHC-6 Twin Otter' WHERE id = 193;
UPDATE aircraft_models SET manufacturer = 'Pilatus Aircraft', model_name = 'PC-12 Eagle' WHERE id = 256;
UPDATE aircraft_models SET manufacturer = 'Saab', model_name = 'SF340A/B' WHERE id = 281;
UPDATE aircraft_models SET manufacturer = 'Embraer', model_name = 'EMB 120 Brasília' WHERE id = 207;
UPDATE aircraft_models SET manufacturer = 'Beechcraft', model_name = '1900 / 1900C / 1900D' WHERE id = 115;
UPDATE aircraft_models SET manufacturer = 'Beechcraft', model_name = 'King Air 350' WHERE id = 123;
UPDATE aircraft_models SET manufacturer = 'Dassault', model_name = 'Falcon 50M' WHERE id = 188;

COMMIT;
