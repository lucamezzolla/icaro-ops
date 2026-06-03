-- Repair for Icaro Ops v10 Central Africa runway notes.
-- This script is safe to run after the failed v10 patch.
-- It inserts runway notes only for ICAO codes that already exist in airports,
-- so it cannot fail on the airport_runway_source_notes foreign key.

USE icaro_ops;

CREATE TABLE IF NOT EXISTS airport_runway_source_notes (
  airport_icao_code CHAR(4) NOT NULL,
  source_note TEXT NOT NULL,
  data_source_name VARCHAR(120) NULL,
  created_at_utc TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

  PRIMARY KEY (airport_icao_code),

  CONSTRAINT fk_airport_runway_source_notes_airport
    FOREIGN KEY (airport_icao_code)
    REFERENCES airports(icao_code)
    ON UPDATE CASCADE
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TEMPORARY TABLE tmp_central_africa_runway_notes (
  airport_icao_code CHAR(4) NOT NULL PRIMARY KEY,
  source_note TEXT NOT NULL,
  data_source_name VARCHAR(120) NULL
) ENGINE=InnoDB;

INSERT INTO tmp_central_africa_runway_notes (
  airport_icao_code,
  source_note,
  data_source_name
) VALUES
('FNAM', '16/34: 2420 x 39, dirt', 'Wikipedia - List of airports in Angola'),
('FNBG', '14/32: 1600 x 30, asphalt', 'Wikipedia - List of airports in Angola'),
('FNCA', '01/19: 2518 x 32, asphalt', 'Wikipedia - List of airports in Angola'),
('FNCC', '11/29: 2042 x 59, dirt', 'Wikipedia - List of airports in Angola'),
('FNCF', '06/24: 2612 x 42, asphalt', 'Wikipedia - List of airports in Angola'),
('FNCM', '17/35: 1411 x 39, grass', 'Wikipedia - List of airports in Angola'),
('FNCX', '11/29: 1996 x 30, gravel', 'Wikipedia - List of airports in Angola'),
('FNCB', '03/21: 1536 x 69, grass', 'Wikipedia - List of airports in Angola'),
('FNCP', '15/33: 2006 x 46, asphalt; H1: 20 dia., grass; H2: 20 dia., grass', 'Wikipedia - List of airports in Angola'),
('FNCT', '02/20: 3716 x 47, asphalt', 'Wikipedia - List of airports in Angola'),
('FNCZ', '17/35: 1975 x 40, dirt', 'Wikipedia - List of airports in Angola'),
('FNCV', '12/30: 2731 x 27, asphalt', 'Wikipedia - List of airports in Angola'),
('FNDB', '14/32: 1237 x 37, grass', 'Wikipedia - List of airports in Angola'),
('FNCH', '13/31: 1792 x 35, asphalt', 'Wikipedia - List of airports in Angola'),
('FNDU', '05/23: 2500 x 45, asphalt', 'Wikipedia - List of airports in Angola'),
('FNNL', '04/22: 457 x 13, dirt', 'Wikipedia - List of airports in Angola'),
('FNHU', '11/29: 2722 x 45, asphalt', 'Wikipedia - List of airports in Angola'),
('FNKU', '07/25: 2493 x 30, asphalt', 'Wikipedia - List of airports in Angola'),
('FNLB', '16/34: 1521 x 30, asphalt', 'Wikipedia - List of airports in Angola'),
('FNLU', '05/23: 3712 x 43, asphalt; 07/25: 2490 x 51, asphalt', 'Wikipedia - List of airports in Angola'),
('FNBJ', '06L/24R: 3800 x 60, asphalt; 06R/24L: 4000 x 60, asphalt', 'Wikipedia - List of airports in Angola'),
('FNUA', '17/35: 1558 x 39, dirt', 'Wikipedia - List of airports in Angola'),
('FNUB', '10/28: 2859 x 29, asphalt', 'Wikipedia - List of airports in Angola'),
('FNLK', '18/36: 2414 x 48, dirt', 'Wikipedia - List of airports in Angola'),
('FNUE', '11/29: 2393 x 30, asphalt', 'Wikipedia - List of airports in Angola'),
('FNBL', '10/28: 1966 x 35, dirt', 'Wikipedia - List of airports in Angola'),
('FNLZ', '03/21: 1588 x 61, asphalt', 'Wikipedia - List of airports in Angola'),
('FNMA', '13/31: 2204 x 32, asphalt', 'Wikipedia - List of airports in Angola'),
('FNMQ', '07/25: 1469 x 39, grass', 'Wikipedia - List of airports in Angola'),
('FNBC', '17/35: 1832 x 30, asphalt', 'Wikipedia - List of airports in Angola'),
('FNME', '13/31: 3560 x 40, asphalt', 'Wikipedia - List of airports in Angola'),
('FNZE', '04/22: 2192 x 27, grass', 'Wikipedia - List of airports in Angola'),
('FNMO', '08/26: 2496 x 45, asphalt', 'Wikipedia - List of airports in Angola'),
('FNNG', '16/34: 2460 x 33, asphalt; 09/27: 814 x 27, dirt', 'Wikipedia - List of airports in Angola'),
('FNZG', '08/26: 2207 x 53, dirt', 'Wikipedia - List of airports in Angola'),
('FNGI', '12/30: 3295 x 35, asphalt', 'Wikipedia - List of airports in Angola'),
('FNPA', '06/24: 991 x 30, asphalt', 'Wikipedia - List of airports in Angola'),
('FNPB', '08/26: 1146 x 36, grass', 'Wikipedia - List of airports in Angola'),
('FNSA', '14/32: 3402 x 45, asphalt', 'Wikipedia - List of airports in Angola'),
('FNSO', '07/25: 2121 x 50, asphalt', 'Wikipedia - List of airports in Angola'),
('FNSU', '05/23: 951 x 22, asphalt', 'Wikipedia - List of airports in Angola'),
('FNTO', '11/29: 1548 x 36, grass', 'Wikipedia - List of airports in Angola'),
('FNUG', '01/19: 2006 x 31, asphalt', 'Wikipedia - List of airports in Angola'),
('FNWK', '07/25: 1993 x 32, asphalt', 'Wikipedia - List of airports in Angola'),
('FNXA', '03/21: 2265 x 30, asphalt', 'Wikipedia - List of airports in Angola'),
('FTTC', 'RWY 09/27; length 2800 m; asphalt', 'Wikipedia - List of airports in Chad'),
('FTTN', 'RWY 03/21; length 1500 m; brick', 'Wikipedia - List of airports in Chad'),
('FTAA', 'RWY 09/27; length 3050 m; asphalt', 'Wikipedia - List of airports in Chad'),
('FTTI', 'RWY 09/27; length 1300 m; brick/sand', 'Wikipedia - List of airports in Chad'),
('FTTE', 'RWY 09/27; length 1250 m; clay', 'Wikipedia - List of airports in Chad'),
('FTTK', 'RWY 09/27; length 1145 m; laterite/brick', 'Wikipedia - List of airports in Chad'),
('FTTL', 'RWY 05/23; length 800 m; macadam', 'Wikipedia - List of airports in Chad'),
('FTTB', 'RWY 09/27; length 1600 m; rolled', 'Wikipedia - List of airports in Chad'),
('FTTS', 'RWY 03/21; length 1200 m; brick', 'Wikipedia - List of airports in Chad'),
('FTTF', 'RWY 12/30; length 1800 m; laterite', 'Wikipedia - List of airports in Chad'),
('FTTY', 'RWY 06/24; length 2800 m; macadam', 'Wikipedia - List of airports in Chad'),
('FTTG', 'RWY 17/35; length 1400 m; clay', 'Wikipedia - List of airports in Chad'),
('FTTH', 'RWY 05/23; length 800 m; laterite', 'Wikipedia - List of airports in Chad'),
('FTTU', 'RWY 07/25; length 1100 m; brick', 'Wikipedia - List of airports in Chad'),
('FTTM', 'RWY 06/24; length 1800 m; clay/sand', 'Wikipedia - List of airports in Chad'),
('FTTD', 'RWY 04/22; length 3000 m; asphalt', 'Wikipedia - List of airports in Chad'),
('FTTJ', 'RWY 05/23; lengths 2800 m and 1500 m; asphalt/concrete/clay', 'Wikipedia - List of airports in Chad'),
('FTTP', 'RWY 05/23; length 1600 m; laterite', 'Wikipedia - List of airports in Chad'),
('FTTA', 'RWY 09/27; length 1800 m; laterite', 'Wikipedia - List of airports in Chad'),
('FTTR', 'RWY 13/31; length 1450 m; gravel', 'Wikipedia - List of airports in Chad'),
('FTTZ', 'RWY 07/25; length 1800 m; sand/gravel', 'Wikipedia - List of airports in Chad')
ON DUPLICATE KEY UPDATE
  source_note = VALUES(source_note),
  data_source_name = VALUES(data_source_name);

INSERT INTO airport_runway_source_notes (
  airport_icao_code,
  source_note,
  data_source_name
)
SELECT
  t.airport_icao_code,
  t.source_note,
  t.data_source_name
FROM tmp_central_africa_runway_notes t
JOIN airports a
  ON a.icao_code = t.airport_icao_code
ON DUPLICATE KEY UPDATE
  source_note = VALUES(source_note),
  data_source_name = VALUES(data_source_name);

-- Diagnostic: rows listed here were NOT inserted because the airport does not exist.
SELECT
  t.airport_icao_code AS missing_airport_icao_code,
  t.source_note,
  t.data_source_name
FROM tmp_central_africa_runway_notes t
LEFT JOIN airports a
  ON a.icao_code = t.airport_icao_code
WHERE a.icao_code IS NULL
ORDER BY t.airport_icao_code;

-- Diagnostic: total airport count after the v10 airport import.
SELECT COUNT(*) AS total_airports
FROM airports;

-- Diagnostic: Central Africa country totals.
SELECT
  c.name AS country_name,
  COUNT(*) AS total_airports
FROM airports a
JOIN countries c
  ON c.id = a.country_id
WHERE c.name IN ('Angola', 'Cameroon', 'Chad', 'Central African Republic')
  AND c.world_region_code = 'AFRICA'
GROUP BY c.name
ORDER BY c.name;
