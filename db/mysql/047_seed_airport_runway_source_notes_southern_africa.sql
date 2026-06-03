-- Safe runway source notes for Eswatini and selected Botswana rows.

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
SELECT 'FBPM' AS airport_icao_code, 'International / military air base' AS source_note, 'Wikipedia - List of airports in Botswana' AS data_source_name
UNION ALL
SELECT 'FBMG' AS airport_icao_code, 'Military airstrip' AS source_note, 'Wikipedia - List of airports in Botswana' AS data_source_name
UNION ALL
SELECT 'FBML' AS airport_icao_code, 'Former airport' AS source_note, 'Wikipedia - List of airports in Botswana' AS data_source_name
UNION ALL
SELECT 'FBSR' AS airport_icao_code, 'Former airport' AS source_note, 'Wikipedia - List of airports in Botswana' AS data_source_name
UNION ALL
SELECT 'FBSK' AS airport_icao_code, 'International / military air base' AS source_note, 'Wikipedia - List of airports in Botswana' AS data_source_name
UNION ALL
SELECT 'FDBT' AS airport_icao_code, '800 m (2,600 ft) Grass' AS source_note, 'Wikipedia - List of airports in Eswatini' AS data_source_name
UNION ALL
SELECT 'FDUB' AS airport_icao_code, '730 m (2,400 ft) unpaved' AS source_note, 'Wikipedia - List of airports in Eswatini' AS data_source_name
UNION ALL
SELECT 'FDKS' AS airport_icao_code, '847 m (2,779 ft) grass; alternate ICAO FDKB' AS source_note, 'Wikipedia - List of airports in Eswatini' AS data_source_name
UNION ALL
SELECT 'FDMS' AS airport_icao_code, '2,600 m (8,500 ft) paved' AS source_note, 'Wikipedia - List of airports in Eswatini' AS data_source_name
UNION ALL
SELECT 'FDSK' AS airport_icao_code, '3,600 m (11,800 ft) Asphalt' AS source_note, 'Wikipedia - List of airports in Eswatini' AS data_source_name
UNION ALL
SELECT 'FDMH' AS airport_icao_code, '709 m (2,326 ft) unpaved' AS source_note, 'Wikipedia - List of airports in Eswatini' AS data_source_name
UNION ALL
SELECT 'FDNG' AS airport_icao_code, '823 m (2,700 ft) unpaved' AS source_note, 'Wikipedia - List of airports in Eswatini' AS data_source_name
UNION ALL
SELECT 'FDNH' AS airport_icao_code, '671 m (2,201 ft) unpaved' AS source_note, 'Wikipedia - List of airports in Eswatini' AS data_source_name
UNION ALL
SELECT 'FDNS' AS airport_icao_code, '671 m (2,201 ft) unpaved' AS source_note, 'Wikipedia - List of airports in Eswatini' AS data_source_name
UNION ALL
SELECT 'FDSM' AS airport_icao_code, '1,100 m (3,600 ft) unpaved' AS source_note, 'Wikipedia - List of airports in Eswatini' AS data_source_name
UNION ALL
SELECT 'FDST' AS airport_icao_code, '1,006 m (3,301 ft) unpaved' AS source_note, 'Wikipedia - List of airports in Eswatini' AS data_source_name
UNION ALL
SELECT 'FDTM' AS airport_icao_code, '875 m (2,871 ft) unpaved' AS source_note, 'Wikipedia - List of airports in Eswatini' AS data_source_name
UNION ALL
SELECT 'FDTS' AS airport_icao_code, '756 m (2,480 ft) unpaved' AS source_note, 'Wikipedia - List of airports in Eswatini' AS data_source_name
) s
JOIN airports a
  ON a.icao_code = s.airport_icao_code
ON DUPLICATE KEY UPDATE
  source_note = VALUES(source_note),
  data_source_name = VALUES(data_source_name);
