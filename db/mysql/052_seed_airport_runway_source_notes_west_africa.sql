-- Safe runway source notes for Banjul and Burkina Faso.

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
SELECT 'GBYD' AS airport_icao_code, '14/32: 3,600 m / 11,811 ft, asphalt' AS source_note, 'Wikipedia - List of airports in The Gambia' AS data_source_name
UNION ALL
SELECT 'DFOY' AS airport_icao_code, 'Grass' AS source_note, 'Wikipedia - List of airports in Burkina Faso' AS data_source_name
UNION ALL
SELECT 'DFER' AS airport_icao_code, '03/21: 4,400 x 118, grass' AS source_note, 'Wikipedia - List of airports in Burkina Faso' AS data_source_name
UNION ALL
SELECT 'DFOB' AS airport_icao_code, '03/21: 3,750 x 59, grass' AS source_note, 'Wikipedia - List of airports in Burkina Faso' AS data_source_name
UNION ALL
SELECT 'DFCB' AS airport_icao_code, '05/23: 1,920 x 69, grass' AS source_note, 'Wikipedia - List of airports in Burkina Faso' AS data_source_name
UNION ALL
SELECT 'DFOO' AS airport_icao_code, '06/24: 10,800 x 138, asphalt' AS source_note, 'Wikipedia - List of airports in Burkina Faso' AS data_source_name
UNION ALL
SELECT 'DFEB' AS airport_icao_code, '11/29: 2,610 x 72, grass' AS source_note, 'Wikipedia - List of airports in Burkina Faso' AS data_source_name
UNION ALL
SELECT 'DFCO' AS airport_icao_code, '07/25: 1,250 x 62, dirt' AS source_note, 'Wikipedia - List of airports in Burkina Faso' AS data_source_name
UNION ALL
SELECT 'DFEA' AS airport_icao_code, '05/23: 1,530 x 66, dirt' AS source_note, 'Wikipedia - List of airports in Burkina Faso' AS data_source_name
UNION ALL
SELECT 'DFOA' AS airport_icao_code, '06/24: 1,800 x 69, grass' AS source_note, 'Wikipedia - List of airports in Burkina Faso' AS data_source_name
UNION ALL
SELECT 'DFOD' AS airport_icao_code, '06/24: 8,480 x 105, grass' AS source_note, 'Wikipedia - List of airports in Burkina Faso' AS data_source_name
UNION ALL
SELECT 'DFED' AS airport_icao_code, '04/22: 3,900 x 98, dirt' AS source_note, 'Wikipedia - List of airports in Burkina Faso' AS data_source_name
UNION ALL
SELECT 'DFCD' AS airport_icao_code, '13/31: 1,500 x 52, grass' AS source_note, 'Wikipedia - List of airports in Burkina Faso' AS data_source_name
UNION ALL
SELECT 'DFOU' AS airport_icao_code, '07/25: 5,250 x 69, dirt' AS source_note, 'Wikipedia - List of airports in Burkina Faso' AS data_source_name
UNION ALL
SELECT 'DFCJ' AS airport_icao_code, '04/22: 3,900 x 92, dirt' AS source_note, 'Wikipedia - List of airports in Burkina Faso' AS data_source_name
UNION ALL
SELECT 'DFEE' AS airport_icao_code, '05/23: 2,300 x 98, dirt' AS source_note, 'Wikipedia - List of airports in Burkina Faso' AS data_source_name
UNION ALL
SELECT 'DFEF' AS airport_icao_code, '04/22: 3,250 x 59, dirt' AS source_note, 'Wikipedia - List of airports in Burkina Faso' AS data_source_name
UNION ALL
SELECT 'DFOG' AS airport_icao_code, '06/24: 4,900 x 102, grass' AS source_note, 'Wikipedia - List of airports in Burkina Faso' AS data_source_name
UNION ALL
SELECT 'DFEG' AS airport_icao_code, '05/23: 5,410 x 105, grass' AS source_note, 'Wikipedia - List of airports in Burkina Faso' AS data_source_name
UNION ALL
SELECT 'DFOH' AS airport_icao_code, '18/36: 1,920 x 89, gravel; 08/26: 2,560 x 79, grass' AS source_note, 'Wikipedia - List of airports in Burkina Faso' AS data_source_name
UNION ALL
SELECT 'DFEL' AS airport_icao_code, '06/24: 2,990 x 46, dirt' AS source_note, 'Wikipedia - List of airports in Burkina Faso' AS data_source_name
UNION ALL
SELECT 'DFCA' AS airport_icao_code, '08/26: 1,960 x 92, grass' AS source_note, 'Wikipedia - List of airports in Burkina Faso' AS data_source_name
UNION ALL
SELECT 'DFCG' AS airport_icao_code, '07/25: 2,600 x 66, grass' AS source_note, 'Wikipedia - List of airports in Burkina Faso' AS data_source_name
UNION ALL
SELECT 'DFCK' AS airport_icao_code, '06/24: 2,940 x 118, grass' AS source_note, 'Wikipedia - List of airports in Burkina Faso' AS data_source_name
UNION ALL
SELECT 'DFCL' AS airport_icao_code, '08/26: 1,380 x 69, grass' AS source_note, 'Wikipedia - List of airports in Burkina Faso' AS data_source_name
UNION ALL
SELECT 'DFON' AS airport_icao_code, '09/27: 4,250 x 141, grass' AS source_note, 'Wikipedia - List of airports in Burkina Faso' AS data_source_name
UNION ALL
SELECT 'DFOR' AS airport_icao_code, '04/22: 4,900 x 105, grass' AS source_note, 'Wikipedia - List of airports in Burkina Faso' AS data_source_name
UNION ALL
SELECT 'DFFD' AS airport_icao_code, '04L/22R: 9,900 x 148, asphalt; 04R/22L: 6,200 x 89, grass' AS source_note, 'Wikipedia - List of airports in Burkina Faso' AS data_source_name
UNION ALL
SELECT 'DFCC' AS airport_icao_code, '09/27: 5,550 x 105, grass' AS source_note, 'Wikipedia - List of airports in Burkina Faso' AS data_source_name
UNION ALL
SELECT 'DFEP' AS airport_icao_code, '09/27: 2,480 x 89, grass' AS source_note, 'Wikipedia - List of airports in Burkina Faso' AS data_source_name
UNION ALL
SELECT 'DFCP' AS airport_icao_code, '10/28: 3,460 x 79, dirt' AS source_note, 'Wikipedia - List of airports in Burkina Faso' AS data_source_name
UNION ALL
SELECT 'DFCR' AS airport_icao_code, '09/27: 1,960 x 85, grass' AS source_note, 'Wikipedia - List of airports in Burkina Faso' AS data_source_name
UNION ALL
SELECT 'DFES' AS airport_icao_code, 'Grass' AS source_note, 'Wikipedia - List of airports in Burkina Faso' AS data_source_name
UNION ALL
SELECT 'DFCS' AS airport_icao_code, '10/28: 1,450 x 92, dirt' AS source_note, 'Wikipedia - List of airports in Burkina Faso' AS data_source_name
UNION ALL
SELECT 'DFET' AS airport_icao_code, '17/35: 3,950 x 125, dirt' AS source_note, 'Wikipedia - List of airports in Burkina Faso' AS data_source_name
UNION ALL
SELECT 'DFOT' AS airport_icao_code, '10/28: 1,950 x 95, grass' AS source_note, 'Wikipedia - List of airports in Burkina Faso' AS data_source_name
UNION ALL
SELECT 'DFCY' AS airport_icao_code, '07/25: 2,900 x 174, grass' AS source_note, 'Wikipedia - List of airports in Burkina Faso' AS data_source_name
UNION ALL
SELECT 'DFEZ' AS airport_icao_code, '18/36' AS source_note, 'Wikipedia - List of airports in Burkina Faso' AS data_source_name
) s
JOIN airports a
  ON a.icao_code = s.airport_icao_code
ON DUPLICATE KEY UPDATE
  source_note = VALUES(source_note),
  data_source_name = VALUES(data_source_name);
