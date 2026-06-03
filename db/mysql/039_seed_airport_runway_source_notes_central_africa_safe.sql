-- Safe runway source notes for Angola and Chad.
-- Inserts notes only for airports that exist, avoiding foreign key errors.

USE icaro_ops;

INSERT INTO airport_runway_source_notes (
  airport_icao_code,
  source_note,
  data_source_name
)
SELECT
  s.airport_icao_code,
  s.source_note,
  s.data_source_name
FROM (
SELECT 'FNAM' AS airport_icao_code, '16/34: 2420 x 39, dirt' AS source_note, 'Wikipedia - List of airports in Angola' AS data_source_name
UNION ALL
SELECT 'FNBG' AS airport_icao_code, '14/32: 1600 x 30, asphalt' AS source_note, 'Wikipedia - List of airports in Angola' AS data_source_name
UNION ALL
SELECT 'FNCA' AS airport_icao_code, '01/19: 2518 x 32, asphalt' AS source_note, 'Wikipedia - List of airports in Angola' AS data_source_name
UNION ALL
SELECT 'FNCC' AS airport_icao_code, '11/29: 2042 x 59, dirt' AS source_note, 'Wikipedia - List of airports in Angola' AS data_source_name
UNION ALL
SELECT 'FNCF' AS airport_icao_code, '06/24: 2612 x 42, asphalt' AS source_note, 'Wikipedia - List of airports in Angola' AS data_source_name
UNION ALL
SELECT 'FNCM' AS airport_icao_code, '17/35: 1411 x 39, grass' AS source_note, 'Wikipedia - List of airports in Angola' AS data_source_name
UNION ALL
SELECT 'FNCX' AS airport_icao_code, '11/29: 1996 x 30, gravel' AS source_note, 'Wikipedia - List of airports in Angola' AS data_source_name
UNION ALL
SELECT 'FNCB' AS airport_icao_code, '03/21: 1536 x 69, grass' AS source_note, 'Wikipedia - List of airports in Angola' AS data_source_name
UNION ALL
SELECT 'FNCP' AS airport_icao_code, '15/33: 2006 x 46, asphalt; H1: 20 dia., grass; H2: 20 dia., grass' AS source_note, 'Wikipedia - List of airports in Angola' AS data_source_name
UNION ALL
SELECT 'FNCT' AS airport_icao_code, '02/20: 3716 x 47, asphalt' AS source_note, 'Wikipedia - List of airports in Angola' AS data_source_name
UNION ALL
SELECT 'FNCZ' AS airport_icao_code, '17/35: 1975 x 40, dirt' AS source_note, 'Wikipedia - List of airports in Angola' AS data_source_name
UNION ALL
SELECT 'FNCV' AS airport_icao_code, '12/30: 2731 x 27, asphalt' AS source_note, 'Wikipedia - List of airports in Angola' AS data_source_name
UNION ALL
SELECT 'FNDB' AS airport_icao_code, '14/32: 1237 x 37, grass' AS source_note, 'Wikipedia - List of airports in Angola' AS data_source_name
UNION ALL
SELECT 'FNCH' AS airport_icao_code, '13/31: 1792 x 35, asphalt' AS source_note, 'Wikipedia - List of airports in Angola' AS data_source_name
UNION ALL
SELECT 'FNDU' AS airport_icao_code, '05/23: 2500 x 45, asphalt' AS source_note, 'Wikipedia - List of airports in Angola' AS data_source_name
UNION ALL
SELECT 'FNNL' AS airport_icao_code, '04/22: 457 x 13, dirt' AS source_note, 'Wikipedia - List of airports in Angola' AS data_source_name
UNION ALL
SELECT 'FNHU' AS airport_icao_code, '11/29: 2722 x 45, asphalt' AS source_note, 'Wikipedia - List of airports in Angola' AS data_source_name
UNION ALL
SELECT 'FNKU' AS airport_icao_code, '07/25: 2493 x 30, asphalt' AS source_note, 'Wikipedia - List of airports in Angola' AS data_source_name
UNION ALL
SELECT 'FNLB' AS airport_icao_code, '16/34: 1521 x 30, asphalt' AS source_note, 'Wikipedia - List of airports in Angola' AS data_source_name
UNION ALL
SELECT 'FNLU' AS airport_icao_code, '05/23: 3712 x 43, asphalt; 07/25: 2490 x 51, asphalt' AS source_note, 'Wikipedia - List of airports in Angola' AS data_source_name
UNION ALL
SELECT 'FNBJ' AS airport_icao_code, '06L/24R: 3800 x 60, asphalt; 06R/24L: 4000 x 60, asphalt' AS source_note, 'Wikipedia - List of airports in Angola' AS data_source_name
UNION ALL
SELECT 'FNUA' AS airport_icao_code, '17/35: 1558 x 39, dirt' AS source_note, 'Wikipedia - List of airports in Angola' AS data_source_name
UNION ALL
SELECT 'FNUB' AS airport_icao_code, '10/28: 2859 x 29, asphalt' AS source_note, 'Wikipedia - List of airports in Angola' AS data_source_name
UNION ALL
SELECT 'FNLK' AS airport_icao_code, '18/36: 2414 x 48, dirt' AS source_note, 'Wikipedia - List of airports in Angola' AS data_source_name
UNION ALL
SELECT 'FNUE' AS airport_icao_code, '11/29: 2393 x 30, asphalt' AS source_note, 'Wikipedia - List of airports in Angola' AS data_source_name
UNION ALL
SELECT 'FNBL' AS airport_icao_code, '10/28: 1966 x 35, dirt' AS source_note, 'Wikipedia - List of airports in Angola' AS data_source_name
UNION ALL
SELECT 'FNLZ' AS airport_icao_code, '03/21: 1588 x 61, asphalt' AS source_note, 'Wikipedia - List of airports in Angola' AS data_source_name
UNION ALL
SELECT 'FNMA' AS airport_icao_code, '13/31: 2204 x 32, asphalt' AS source_note, 'Wikipedia - List of airports in Angola' AS data_source_name
UNION ALL
SELECT 'FNMQ' AS airport_icao_code, '07/25: 1469 x 39, grass' AS source_note, 'Wikipedia - List of airports in Angola' AS data_source_name
UNION ALL
SELECT 'FNBC' AS airport_icao_code, '17/35: 1832 x 30, asphalt' AS source_note, 'Wikipedia - List of airports in Angola' AS data_source_name
UNION ALL
SELECT 'FNME' AS airport_icao_code, '13/31: 3560 x 40, asphalt' AS source_note, 'Wikipedia - List of airports in Angola' AS data_source_name
UNION ALL
SELECT 'FNZE' AS airport_icao_code, '04/22: 2192 x 27, grass' AS source_note, 'Wikipedia - List of airports in Angola' AS data_source_name
UNION ALL
SELECT 'FNMO' AS airport_icao_code, '08/26: 2496 x 45, asphalt' AS source_note, 'Wikipedia - List of airports in Angola' AS data_source_name
UNION ALL
SELECT 'FNNG' AS airport_icao_code, '16/34: 2460 x 33, asphalt; 09/27: 814 x 27, dirt' AS source_note, 'Wikipedia - List of airports in Angola' AS data_source_name
UNION ALL
SELECT 'FNZG' AS airport_icao_code, '08/26: 2207 x 53, dirt' AS source_note, 'Wikipedia - List of airports in Angola' AS data_source_name
UNION ALL
SELECT 'FNGI' AS airport_icao_code, '12/30: 3295 x 35, asphalt' AS source_note, 'Wikipedia - List of airports in Angola' AS data_source_name
UNION ALL
SELECT 'FNPA' AS airport_icao_code, '06/24: 991 x 30, asphalt' AS source_note, 'Wikipedia - List of airports in Angola' AS data_source_name
UNION ALL
SELECT 'FNPB' AS airport_icao_code, '08/26: 1146 x 36, grass' AS source_note, 'Wikipedia - List of airports in Angola' AS data_source_name
UNION ALL
SELECT 'FNSA' AS airport_icao_code, '14/32: 3402 x 45, asphalt' AS source_note, 'Wikipedia - List of airports in Angola' AS data_source_name
UNION ALL
SELECT 'FNSO' AS airport_icao_code, '07/25: 2121 x 50, asphalt' AS source_note, 'Wikipedia - List of airports in Angola' AS data_source_name
UNION ALL
SELECT 'FNSU' AS airport_icao_code, '05/23: 951 x 22, asphalt' AS source_note, 'Wikipedia - List of airports in Angola' AS data_source_name
UNION ALL
SELECT 'FNTO' AS airport_icao_code, '11/29: 1548 x 36, grass' AS source_note, 'Wikipedia - List of airports in Angola' AS data_source_name
UNION ALL
SELECT 'FNUG' AS airport_icao_code, '01/19: 2006 x 31, asphalt' AS source_note, 'Wikipedia - List of airports in Angola' AS data_source_name
UNION ALL
SELECT 'FNWK' AS airport_icao_code, '07/25: 1993 x 32, asphalt' AS source_note, 'Wikipedia - List of airports in Angola' AS data_source_name
UNION ALL
SELECT 'FNXA' AS airport_icao_code, '03/21: 2265 x 30, asphalt' AS source_note, 'Wikipedia - List of airports in Angola' AS data_source_name
UNION ALL
SELECT 'FTTC' AS airport_icao_code, 'RWY 09/27; length 2800 m; asphalt' AS source_note, 'Wikipedia - List of airports in Chad' AS data_source_name
UNION ALL
SELECT 'FTTN' AS airport_icao_code, 'RWY 03/21; length 1500 m; brick' AS source_note, 'Wikipedia - List of airports in Chad' AS data_source_name
UNION ALL
SELECT 'FTAA' AS airport_icao_code, 'RWY 09/27; length 3050 m; asphalt' AS source_note, 'Wikipedia - List of airports in Chad' AS data_source_name
UNION ALL
SELECT 'FTTI' AS airport_icao_code, 'RWY 09/27; length 1300 m; brick/sand' AS source_note, 'Wikipedia - List of airports in Chad' AS data_source_name
UNION ALL
SELECT 'FTTE' AS airport_icao_code, 'RWY 09/27; length 1250 m; clay' AS source_note, 'Wikipedia - List of airports in Chad' AS data_source_name
UNION ALL
SELECT 'FTTK' AS airport_icao_code, 'RWY 09/27; length 1145 m; laterite/brick' AS source_note, 'Wikipedia - List of airports in Chad' AS data_source_name
UNION ALL
SELECT 'FTTL' AS airport_icao_code, 'RWY 05/23; length 800 m; macadam' AS source_note, 'Wikipedia - List of airports in Chad' AS data_source_name
UNION ALL
SELECT 'FTTB' AS airport_icao_code, 'RWY 09/27; length 1600 m; rolled' AS source_note, 'Wikipedia - List of airports in Chad' AS data_source_name
UNION ALL
SELECT 'FTTS' AS airport_icao_code, 'RWY 03/21; length 1200 m; brick' AS source_note, 'Wikipedia - List of airports in Chad' AS data_source_name
UNION ALL
SELECT 'FTTF' AS airport_icao_code, 'RWY 12/30; length 1800 m; laterite' AS source_note, 'Wikipedia - List of airports in Chad' AS data_source_name
UNION ALL
SELECT 'FTTY' AS airport_icao_code, 'RWY 06/24; length 2800 m; macadam' AS source_note, 'Wikipedia - List of airports in Chad' AS data_source_name
UNION ALL
SELECT 'FTTG' AS airport_icao_code, 'RWY 17/35; length 1400 m; clay' AS source_note, 'Wikipedia - List of airports in Chad' AS data_source_name
UNION ALL
SELECT 'FTTH' AS airport_icao_code, 'RWY 05/23; length 800 m; laterite' AS source_note, 'Wikipedia - List of airports in Chad' AS data_source_name
UNION ALL
SELECT 'FTTU' AS airport_icao_code, 'RWY 07/25; length 1100 m; brick' AS source_note, 'Wikipedia - List of airports in Chad' AS data_source_name
UNION ALL
SELECT 'FTTM' AS airport_icao_code, 'RWY 06/24; length 1800 m; clay/sand' AS source_note, 'Wikipedia - List of airports in Chad' AS data_source_name
UNION ALL
SELECT 'FTTD' AS airport_icao_code, 'RWY 04/22; length 3000 m; asphalt' AS source_note, 'Wikipedia - List of airports in Chad' AS data_source_name
UNION ALL
SELECT 'FTTJ' AS airport_icao_code, 'RWY 05/23; lengths 2800 m and 1500 m; asphalt/concrete/clay' AS source_note, 'Wikipedia - List of airports in Chad' AS data_source_name
UNION ALL
SELECT 'FTTP' AS airport_icao_code, 'RWY 05/23; length 1600 m; laterite' AS source_note, 'Wikipedia - List of airports in Chad' AS data_source_name
UNION ALL
SELECT 'FTTA' AS airport_icao_code, 'RWY 09/27; length 1800 m; laterite' AS source_note, 'Wikipedia - List of airports in Chad' AS data_source_name
UNION ALL
SELECT 'FTTR' AS airport_icao_code, 'RWY 13/31; length 1450 m; gravel' AS source_note, 'Wikipedia - List of airports in Chad' AS data_source_name
UNION ALL
SELECT 'FTTZ' AS airport_icao_code, 'RWY 07/25; length 1800 m; sand/gravel' AS source_note, 'Wikipedia - List of airports in Chad' AS data_source_name
) s
JOIN airports a
  ON a.icao_code = s.airport_icao_code
ON DUPLICATE KEY UPDATE
  source_note = VALUES(source_note),
  data_source_name = VALUES(data_source_name);
