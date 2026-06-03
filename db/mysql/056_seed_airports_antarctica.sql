-- Antarctica airport / skiway / heliport seed batch.
-- Source: List of airports in Antarctica.
--
-- Import rule:
--   - airports.icao_code remains the primary key.
--   - Source ICAO code is used when present.
--   - If ICAO is missing, a clean 4-character source "Other code" is used.
--   - Rows without a 4-character usable primary code are documented but not imported.

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

CREATE TEMPORARY TABLE tmp_antarctica_airports (
  country_name VARCHAR(120) NOT NULL,
  icao_prefix VARCHAR(8) NOT NULL,
  icao_code CHAR(4) NOT NULL,
  iata_code CHAR(3) NULL,
  name VARCHAR(200) NOT NULL,
  city VARCHAR(160) NULL,
  location_name VARCHAR(160) NULL,
  subdivision_name VARCHAR(120) NULL,
  latitude DECIMAL(10,7) NOT NULL,
  longitude DECIMAL(10,7) NOT NULL,
  elevation_ft INT NULL,
  airport_type VARCHAR(40) NOT NULL,
  service_category VARCHAR(40) NOT NULL,
  is_closed BOOLEAN NOT NULL DEFAULT FALSE,
  operator_country_name VARCHAR(120) NULL,
  data_source_name VARCHAR(120) NULL,
  data_source_url VARCHAR(255) NULL,
  data_quality VARCHAR(40) NOT NULL,

  PRIMARY KEY (icao_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO tmp_antarctica_airports (
  country_name,
  icao_prefix,
  icao_code,
  iata_code,
  name,
  city,
  location_name,
  subdivision_name,
  latitude,
  longitude,
  elevation_ft,
  airport_type,
  service_category,
  is_closed,
  operator_country_name,
  data_source_name,
  data_source_url,
  data_quality
) VALUES
('Antarctica', 'SA', 'SAYB', NULL, 'Belgrano II Skiway', 'Bertrab Nunatak', 'Bertrab Nunatak', NULL, -64.9755556, -60.0713889, NULL, 'AIRFIELD', 'NATIONAL', FALSE, 'Argentina', 'Wikipedia - List of airports in Antarctica', 'https://en.wikipedia.org/wiki/List_of_airports_in_Antarctica', 'PARTIAL'),
('Antarctica', 'AQ', 'AQBC', NULL, 'Boulder Clay Runway (serving Zucchelli)', 'Terra Nova Bay', 'Terra Nova Bay', NULL, -74.74, 164.0372222, NULL, 'AIRFIELD', 'NATIONAL', FALSE, 'Italy', 'Wikipedia - List of airports in Antarctica', 'https://en.wikipedia.org/wiki/List_of_airports_in_Antarctica', 'PARTIAL'),
('Antarctica', 'AT', 'AT02', NULL, 'Browning Pass Skiway', 'Terra Nova Bay', 'Terra Nova Bay', NULL, -74.6225, 163.9161111, NULL, 'AIRFIELD', 'NATIONAL', FALSE, 'Italy', 'Wikipedia - List of airports in Antarctica', 'https://en.wikipedia.org/wiki/List_of_airports_in_Antarctica', 'PARTIAL'),
('Antarctica', 'SA', 'SAYJ', NULL, 'Carlini Airstrip', 'Potter Cove', 'Potter Cove', NULL, -62.2383333, -58.6666667, NULL, 'AIRSTRIP', 'NATIONAL', FALSE, 'Argentina', 'Wikipedia - List of airports in Antarctica', 'https://en.wikipedia.org/wiki/List_of_airports_in_Antarctica', 'PARTIAL'),
('Antarctica', 'YC', 'YCSK', NULL, 'Casey Station Skiway (serving Casey)', 'Budd Coast / Wilkes Land', 'Budd Coast / Wilkes Land', NULL, -66.2880556, 110.7575, NULL, 'AIRFIELD', 'NATIONAL', FALSE, 'Australia', 'Wikipedia - List of airports in Antarctica', 'https://en.wikipedia.org/wiki/List_of_airports_in_Antarctica', 'PARTIAL'),
('Antarctica', 'AT', 'AT03', NULL, 'Concordia Skiway', 'Antarctic Plateau', 'Antarctic Plateau', NULL, -75.1033333, 123.3583333, NULL, 'AIRFIELD', 'NATIONAL', FALSE, 'France / Italy', 'Wikipedia - List of airports in Antarctica', 'https://en.wikipedia.org/wiki/List_of_airports_in_Antarctica', 'PARTIAL'),
('Antarctica', 'AT', 'AT04', NULL, 'D10 Skiway (serving Dumont d''Urville Station)', 'Cape Géodésie', 'Cape Géodésie', NULL, -66.6680556, 139.8197222, NULL, 'AIRFIELD', 'NATIONAL', FALSE, 'France', 'Wikipedia - List of airports in Antarctica', 'https://en.wikipedia.org/wiki/List_of_airports_in_Antarctica', 'PARTIAL'),
('Antarctica', 'AT', 'AT05', NULL, 'D85 Skiway', 'Adélie Land', 'Adélie Land', NULL, -70.425, 134.1458333, NULL, 'AIRFIELD', 'NATIONAL', FALSE, 'France', 'Wikipedia - List of airports in Antarctica', 'https://en.wikipedia.org/wiki/List_of_airports_in_Antarctica', 'PARTIAL'),
('Antarctica', 'AT', 'AT07', NULL, 'Davis Plateau Skiway (serving Davis)', 'Princess Elizabeth Land', 'Princess Elizabeth Land', NULL, -68.4697222, 78.7908333, NULL, 'AIRFIELD', 'NATIONAL', FALSE, 'Australia', 'Wikipedia - List of airports in Antarctica', 'https://en.wikipedia.org/wiki/List_of_airports_in_Antarctica', 'PARTIAL'),
('Antarctica', 'AT', 'AT09', NULL, 'Enigma Lake Skiway (serving Mario Zucchelli)', 'Terra Nova Bay', 'Terra Nova Bay', NULL, -74.7188889, 164.0294444, NULL, 'AIRFIELD', 'NATIONAL', FALSE, 'Italy', 'Wikipedia - List of airports in Antarctica', 'https://en.wikipedia.org/wiki/List_of_airports_in_Antarctica', 'PARTIAL'),
('Antarctica', 'AT', 'AT10', NULL, 'Fossil Bluff Skiway', 'George VI Sound', 'George VI Sound', NULL, -71.3294444, -68.2669444, NULL, 'AIRFIELD', 'NATIONAL', FALSE, 'United Kingdom', 'Wikipedia - List of airports in Antarctica', 'https://en.wikipedia.org/wiki/List_of_airports_in_Antarctica', 'PARTIAL'),
('Antarctica', 'EG', 'EGAH', NULL, 'Halley Skiway', 'Brunt Ice Shelf', 'Brunt Ice Shelf', NULL, -75.5816667, -26.5411111, NULL, 'AIRFIELD', 'NATIONAL', FALSE, 'United Kingdom', 'Wikipedia - List of airports in Antarctica', 'https://en.wikipedia.org/wiki/List_of_airports_in_Antarctica', 'PARTIAL'),
('Antarctica', 'NZ', 'NZSP', NULL, 'Jack F. Paulus Skiway (serving Amundsen-Scott South Pole Station)', 'South Pole', 'South Pole', NULL, -89.9975, 139.2727778, NULL, 'AIRFIELD', 'NATIONAL', FALSE, 'United States', 'Wikipedia - List of airports in Antarctica', 'https://en.wikipedia.org/wiki/List_of_airports_in_Antarctica', 'PARTIAL'),
('Antarctica', 'AT', 'AT12', NULL, 'Kohnen Skiway', 'Queen Maud Land', 'Queen Maud Land', NULL, -75.0019444, 0.0666667, NULL, 'AIRFIELD', 'NATIONAL', FALSE, 'Germany', 'Wikipedia - List of airports in Antarctica', 'https://en.wikipedia.org/wiki/List_of_airports_in_Antarctica', 'PARTIAL'),
('Antarctica', 'SA', 'SAWB', NULL, 'Marambio Airport', 'Seymour Island', 'Seymour Island', NULL, -64.2391667, -56.63, NULL, 'AIRPORT', 'NATIONAL', FALSE, 'Argentina', 'Wikipedia - List of airports in Antarctica', 'https://en.wikipedia.org/wiki/List_of_airports_in_Antarctica', 'PARTIAL'),
('Antarctica', 'SA', 'SAWZ', 'BTM', 'Matienzo Skiway', 'Larsen Nunatak', 'Larsen Nunatak', NULL, -64.9755556, -60.0713889, NULL, 'AIRFIELD', 'NATIONAL', FALSE, 'Argentina', 'Wikipedia - List of airports in Antarctica', 'https://en.wikipedia.org/wiki/List_of_airports_in_Antarctica', 'PARTIAL'),
('Antarctica', 'NZ', 'NZIR', NULL, 'McMurdo Ice Runway (serving McMurdo Station and Scott Base)', 'Ross Island', 'Ross Island', NULL, -77.8538889, 166.4686111, NULL, 'AIRFIELD', 'NATIONAL', FALSE, 'United States / New Zealand', 'Wikipedia - List of airports in Antarctica', 'https://en.wikipedia.org/wiki/List_of_airports_in_Antarctica', 'PARTIAL'),
('Antarctica', 'AT', 'AT14', NULL, 'Mid Point Skiway', 'East Antarctic Ice Sheet', 'East Antarctic Ice Sheet', NULL, -75.5411111, 145.8216667, NULL, 'AIRFIELD', 'NATIONAL', FALSE, 'Italy', 'Wikipedia - List of airports in Antarctica', 'https://en.wikipedia.org/wiki/List_of_airports_in_Antarctica', 'PARTIAL'),
('Antarctica', 'AT', 'AT15', NULL, 'Molodezhnaya Ice Runway', 'Thala Hills', 'Thala Hills', NULL, -67.6827778, 46.1347222, NULL, 'AIRFIELD', 'NATIONAL', FALSE, 'Russia', 'Wikipedia - List of airports in Antarctica', 'https://en.wikipedia.org/wiki/List_of_airports_in_Antarctica', 'PARTIAL'),
('Antarctica', 'AT', 'AT16', NULL, 'Neumayer III Skiway', 'Ekstrom Ice Shelf', 'Ekstrom Ice Shelf', NULL, -70.6352778, -8.2636111, NULL, 'AIRFIELD', 'NATIONAL', FALSE, 'Germany', 'Wikipedia - List of airports in Antarctica', 'https://en.wikipedia.org/wiki/List_of_airports_in_Antarctica', 'PARTIAL'),
('Antarctica', 'AT', 'AT17', NULL, 'Novo Runway (serving Novolazarevskaya and Maitri)', 'Queen Maud Land', 'Queen Maud Land', NULL, -70.8213889, 11.6433333, NULL, 'AIRFIELD', 'NATIONAL', FALSE, 'Russia / India', 'Wikipedia - List of airports in Antarctica', 'https://en.wikipedia.org/wiki/List_of_airports_in_Antarctica', 'PARTIAL'),
('Antarctica', 'SC', 'SCBO', NULL, 'O''Higgins Skiway (serving General Bernardo O''Higgins)', 'Prime Head', 'Prime Head', NULL, -63.3427778, -57.8230556, NULL, 'AIRFIELD', 'NATIONAL', FALSE, 'Chile', 'Wikipedia - List of airports in Antarctica', 'https://en.wikipedia.org/wiki/List_of_airports_in_Antarctica', 'PARTIAL'),
('Antarctica', 'AT', 'AT18', NULL, 'Odell Glacier Skiway', 'Odell Glacier', 'Odell Glacier', NULL, -76.65, 159.9666667, NULL, 'AIRFIELD', 'NATIONAL', FALSE, 'United States', 'Wikipedia - List of airports in Antarctica', 'https://en.wikipedia.org/wiki/List_of_airports_in_Antarctica', 'PARTIAL'),
('Antarctica', 'NZ', 'NZ12', NULL, 'Palmer Skiway', 'Anvers Island', 'Anvers Island', NULL, -64.7744444, -64.0358333, NULL, 'AIRFIELD', 'NATIONAL', FALSE, 'United States', 'Wikipedia - List of airports in Antarctica', 'https://en.wikipedia.org/wiki/List_of_airports_in_Antarctica', 'PARTIAL'),
('Antarctica', 'SC', 'SCPZ', NULL, 'Patriot Hills Blue-Ice Runway', 'Ellsworth Mountains', 'Ellsworth Mountains', NULL, -80.3147222, -81.3747222, NULL, 'AIRFIELD', 'NATIONAL', FALSE, 'United States', 'Wikipedia - List of airports in Antarctica', 'https://en.wikipedia.org/wiki/List_of_airports_in_Antarctica', 'PARTIAL'),
('Antarctica', 'NZ', 'NZPG', NULL, 'Pegasus Field (serving McMurdo Station and Scott Base)', 'Ross Island', 'Ross Island', NULL, -77.9744444, 166.5277778, NULL, 'AIRPORT', 'NATIONAL', FALSE, 'United States / New Zealand', 'Wikipedia - List of airports in Antarctica', 'https://en.wikipedia.org/wiki/List_of_airports_in_Antarctica', 'PARTIAL'),
('Antarctica', 'SA', 'SA47', NULL, 'Petrel Skiway', 'Dundee Island', 'Dundee Island', NULL, -63.4788889, -56.2313889, NULL, 'AIRFIELD', 'NATIONAL', FALSE, 'Argentina', 'Wikipedia - List of airports in Antarctica', 'https://en.wikipedia.org/wiki/List_of_airports_in_Antarctica', 'PARTIAL'),
('Antarctica', 'NZ', 'NZFX', NULL, 'Phoenix Airfield (serving McMurdo Station and Scott Base)', 'Ross Island', 'Ross Island', NULL, -77.9563889, 166.7666667, NULL, 'AIRFIELD', 'NATIONAL', FALSE, 'United States / New Zealand', 'Wikipedia - List of airports in Antarctica', 'https://en.wikipedia.org/wiki/List_of_airports_in_Antarctica', 'PARTIAL'),
('Antarctica', 'AT', 'AT20', NULL, 'Plateau Station Skiway', 'Queen Maud Land', 'Queen Maud Land', NULL, -79.2508333, 40.5605556, NULL, 'AIRFIELD', 'NATIONAL', FALSE, 'United States', 'Wikipedia - List of airports in Antarctica', 'https://en.wikipedia.org/wiki/List_of_airports_in_Antarctica', 'PARTIAL'),
('Antarctica', 'AT', 'AT99', NULL, 'Princess Elisabeth Skiway', 'Utsteinen Nunatak', 'Utsteinen Nunatak', NULL, -71.9575, 23.22, NULL, 'AIRFIELD', 'NATIONAL', FALSE, 'Belgium', 'Wikipedia - List of airports in Antarctica', 'https://en.wikipedia.org/wiki/List_of_airports_in_Antarctica', 'PARTIAL'),
('Antarctica', 'SC', 'SCRM', 'TNM', 'Rodolfo Marsh Martin Airport (serving Eduardo Frei)', 'King George Island', 'King George Island', NULL, -62.1908333, -58.9866667, NULL, 'AIRPORT', 'NATIONAL', FALSE, 'Chile', 'Wikipedia - List of airports in Antarctica', 'https://en.wikipedia.org/wiki/List_of_airports_in_Antarctica', 'PARTIAL'),
('Antarctica', 'EG', 'EGAR', NULL, 'Rothera Air Facility', 'Rothera Point / Adelaide Island', 'Rothera Point / Adelaide Island', NULL, -67.5677778, -68.1275, NULL, 'AIRPORT', 'NATIONAL', FALSE, 'United Kingdom', 'Wikipedia - List of airports in Antarctica', 'https://en.wikipedia.org/wiki/List_of_airports_in_Antarctica', 'PARTIAL'),
('Antarctica', 'AT', 'AT21', NULL, 'Rumdoodle Skiway (serving Mawson)', 'Mac. Robertson Land', 'Mac. Robertson Land', NULL, -67.7536111, 62.7661111, NULL, 'AIRFIELD', 'NATIONAL', FALSE, 'Australia', 'Wikipedia - List of airports in Antarctica', 'https://en.wikipedia.org/wiki/List_of_airports_in_Antarctica', 'PARTIAL'),
('Antarctica', 'SA', 'SAYS', 'BSM', 'San Martín Airstrip', 'Marguerite Bay', 'Marguerite Bay', NULL, -68.1166667, -67.1, NULL, 'AIRSTRIP', 'NATIONAL', FALSE, 'Argentina', 'Wikipedia - List of airports in Antarctica', 'https://en.wikipedia.org/wiki/List_of_airports_in_Antarctica', 'PARTIAL'),
('Antarctica', 'AT', 'AT22', NULL, 'SANAE IV Skiway', 'Queen Maud Land', 'Queen Maud Land', NULL, -71.6725, -2.8247222, NULL, 'AIRFIELD', 'NATIONAL', FALSE, 'South Africa', 'Wikipedia - List of airports in Antarctica', 'https://en.wikipedia.org/wiki/List_of_airports_in_Antarctica', 'PARTIAL'),
('Antarctica', 'AT', 'AT25', NULL, 'Showa Skiway', 'East Ongul Island', 'East Ongul Island', NULL, -69.0197222, 39.6252778, NULL, 'AIRFIELD', 'NATIONAL', FALSE, 'Japan', 'Wikipedia - List of airports in Antarctica', 'https://en.wikipedia.org/wiki/List_of_airports_in_Antarctica', 'PARTIAL'),
('Antarctica', 'AT', 'AT23', NULL, 'Sitry Skiway', 'Antarctic Plateau', 'Antarctic Plateau', NULL, -71.6538889, 148.6533333, NULL, 'AIRFIELD', 'NATIONAL', FALSE, 'Italy', 'Wikipedia - List of airports in Antarctica', 'https://en.wikipedia.org/wiki/List_of_airports_in_Antarctica', 'PARTIAL'),
('Antarctica', 'EG', 'EGAT', NULL, 'Sky Blu Skiway', 'Ellsworth Land', 'Ellsworth Land', NULL, -74.8563889, -71.5694444, NULL, 'AIRFIELD', 'NATIONAL', FALSE, 'United Kingdom', 'Wikipedia - List of airports in Antarctica', 'https://en.wikipedia.org/wiki/List_of_airports_in_Antarctica', 'PARTIAL'),
('Antarctica', 'AT', 'AT26', NULL, 'Thiel Skiway', 'Thiel Mountains', 'Thiel Mountains', NULL, -85.1983333, -87.8783333, NULL, 'AIRFIELD', 'NATIONAL', FALSE, NULL, 'Wikipedia - List of airports in Antarctica', 'https://en.wikipedia.org/wiki/List_of_airports_in_Antarctica', 'PARTIAL'),
('Antarctica', 'EN', 'ENOE', NULL, 'Troll Airfield (serving Troll Station)', 'Queen Maud Land', 'Queen Maud Land', NULL, -71.9552778, 2.4675, NULL, 'AIRFIELD', 'NATIONAL', FALSE, 'Norway', 'Wikipedia - List of airports in Antarctica', 'https://en.wikipedia.org/wiki/List_of_airports_in_Antarctica', 'PARTIAL'),
('Antarctica', 'SC', 'SCGC', 'UGL', 'Union Glacier Blue-Ice Runway (serving Union Glacier Camp and Union Glacier Station)', 'Heritage Range', 'Heritage Range', NULL, -79.7777778, -83.3208333, NULL, 'AIRFIELD', 'NATIONAL', FALSE, 'United States / Chile', 'Wikipedia - List of airports in Antarctica', 'https://en.wikipedia.org/wiki/List_of_airports_in_Antarctica', 'PARTIAL'),
('Antarctica', 'AT', 'AT28', NULL, 'Vostok Skiway', 'Pole of Cold', 'Pole of Cold', NULL, -78.4661111, 106.8483333, NULL, 'AIRFIELD', 'NATIONAL', FALSE, 'Russia', 'Wikipedia - List of airports in Antarctica', 'https://en.wikipedia.org/wiki/List_of_airports_in_Antarctica', 'PARTIAL'),
('Antarctica', 'YW', 'YWKS', NULL, 'Wilkins Runway (serving Casey)', 'Budd Coast / Wilkes Land / Upper Peterson Glacier', 'Budd Coast / Wilkes Land / Upper Peterson Glacier', NULL, -66.6894444, 111.4858333, NULL, 'AIRFIELD', 'NATIONAL', FALSE, 'Australia', 'Wikipedia - List of airports in Antarctica', 'https://en.wikipedia.org/wiki/List_of_airports_in_Antarctica', 'PARTIAL'),
('Antarctica', 'NZ', 'NZWD', NULL, 'Williams Field (serving McMurdo Station and Scott Base)', 'Ross Island', 'Ross Island', NULL, -77.8672222, 167.0566667, NULL, 'AIRPORT', 'NATIONAL', FALSE, 'United States / New Zealand', 'Wikipedia - List of airports in Antarctica', 'https://en.wikipedia.org/wiki/List_of_airports_in_Antarctica', 'PARTIAL'),
('Antarctica', 'AT', 'AT98', NULL, 'Wolfs Fang Runway', 'Queen Maud Land', 'Queen Maud Land', NULL, -71.5166667, 8.8, NULL, 'AIRFIELD', 'NATIONAL', FALSE, 'United Kingdom', 'Wikipedia - List of airports in Antarctica', 'https://en.wikipedia.org/wiki/List_of_airports_in_Antarctica', 'PARTIAL'),
('Antarctica', 'NZ', 'NZTB', NULL, 'Zucchelli Ice Runway (serving Zucchelli)', 'Terra Nova Bay', 'Terra Nova Bay', NULL, -74.6830556, 164.1125, NULL, 'AIRFIELD', 'NATIONAL', FALSE, 'Italy', 'Wikipedia - List of airports in Antarctica', 'https://en.wikipedia.org/wiki/List_of_airports_in_Antarctica', 'PARTIAL'),
('Antarctica', 'SA', 'SAYO', NULL, 'Orcadas Heliport', 'Laurie Island', 'Laurie Island', NULL, -60.7380556, -44.7377778, NULL, 'AIRFIELD', 'NATIONAL', FALSE, 'Argentina', 'Wikipedia - List of airports in Antarctica', 'https://en.wikipedia.org/wiki/List_of_airports_in_Antarctica', 'PARTIAL')
ON DUPLICATE KEY UPDATE
  country_name = VALUES(country_name),
  icao_prefix = VALUES(icao_prefix),
  iata_code = VALUES(iata_code),
  name = VALUES(name),
  city = VALUES(city),
  location_name = VALUES(location_name),
  subdivision_name = VALUES(subdivision_name),
  latitude = VALUES(latitude),
  longitude = VALUES(longitude),
  elevation_ft = VALUES(elevation_ft),
  airport_type = VALUES(airport_type),
  service_category = VALUES(service_category),
  is_closed = VALUES(is_closed),
  operator_country_name = VALUES(operator_country_name),
  data_source_name = VALUES(data_source_name),
  data_source_url = VALUES(data_source_url),
  data_quality = VALUES(data_quality);

-- Insert missing prefixes only. Existing prefixes are not overwritten,
-- because prefixes like SA, NZ, EG, SC, EN and YW belong to other ICAO regions/operators.
INSERT INTO icao_prefixes (
  prefix,
  country_id,
  area_name,
  notes
)
SELECT DISTINCT
  t.icao_prefix,
  c.id,
  t.country_name,
  'Antarctica source prefix or source local code prefix.'
FROM tmp_antarctica_airports t
JOIN countries c
  ON c.name = t.country_name
 AND c.world_region_code = 'ANTARCTICA'
LEFT JOIN icao_prefixes p
  ON p.prefix = t.icao_prefix
WHERE p.prefix IS NULL;

INSERT INTO airports (
  icao_code,
  country_id,
  icao_prefix,
  iata_code,
  name,
  city,
  location_name,
  subdivision_name,
  latitude,
  longitude,
  elevation_ft,
  airport_type,
  service_category,
  is_civilian,
  is_commercial,
  is_military,
  is_closed,
  operator_country_name,
  aip_url,
  chart_url,
  source_rating_percent,
  data_source_name,
  data_source_url,
  data_quality
)
SELECT
  t.icao_code,
  c.id,
  t.icao_prefix,
  t.iata_code,
  t.name,
  t.city,
  t.location_name,
  t.subdivision_name,
  t.latitude,
  t.longitude,
  t.elevation_ft,
  t.airport_type,
  t.service_category,
  TRUE,
  FALSE,
  FALSE,
  t.is_closed,
  t.operator_country_name,
  NULL,
  NULL,
  NULL,
  t.data_source_name,
  t.data_source_url,
  t.data_quality
FROM tmp_antarctica_airports t
JOIN countries c
  ON c.name = t.country_name
 AND c.world_region_code = 'ANTARCTICA'
JOIN icao_prefixes p
  ON p.prefix = t.icao_prefix
ON DUPLICATE KEY UPDATE
  country_id = VALUES(country_id),
  icao_prefix = VALUES(icao_prefix),
  iata_code = VALUES(iata_code),
  name = VALUES(name),
  city = VALUES(city),
  location_name = VALUES(location_name),
  subdivision_name = VALUES(subdivision_name),
  latitude = VALUES(latitude),
  longitude = VALUES(longitude),
  elevation_ft = VALUES(elevation_ft),
  airport_type = VALUES(airport_type),
  service_category = VALUES(service_category),
  is_civilian = VALUES(is_civilian),
  is_commercial = VALUES(is_commercial),
  is_military = VALUES(is_military),
  is_closed = VALUES(is_closed),
  operator_country_name = VALUES(operator_country_name),
  aip_url = VALUES(aip_url),
  chart_url = VALUES(chart_url),
  source_rating_percent = VALUES(source_rating_percent),
  data_source_name = VALUES(data_source_name),
  data_source_url = VALUES(data_source_url),
  data_quality = VALUES(data_quality);

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

SELECT 'SAYB' AS airport_icao_code, 'Runway/surface: 6,560 feet (2,000 m), Ice.' AS source_note, 'Wikipedia - List of airports in Antarctica' AS data_source_name
UNION ALL
SELECT 'AQBC' AS airport_icao_code, 'Runway/surface: 02/20, 7,218 feet (2,200 m), Gravel.' AS source_note, 'Wikipedia - List of airports in Antarctica' AS data_source_name
UNION ALL
SELECT 'AT02' AS airport_icao_code, 'Primary code stored from source Other code: AT02. Source other code: AT02. Runway/surface: 02/20, 3,010 feet (920 m), Ice.' AS source_note, 'Wikipedia - List of airports in Antarctica' AS data_source_name
UNION ALL
SELECT 'SAYJ' AS airport_icao_code, 'Runway/surface: 1,312 feet (400 m), Gravel.' AS source_note, 'Wikipedia - List of airports in Antarctica' AS data_source_name
UNION ALL
SELECT 'YCSK' AS airport_icao_code, 'Runway/surface: 09/27, 6,547 feet (1,996 m), Ice.' AS source_note, 'Wikipedia - List of airports in Antarctica' AS data_source_name
UNION ALL
SELECT 'AT03' AS airport_icao_code, 'Primary code stored from source Other code: AT03. Source other code: AT03. Runway/surface: 01/19, 6,560 feet (2,000 m), Ice.' AS source_note, 'Wikipedia - List of airports in Antarctica' AS data_source_name
UNION ALL
SELECT 'AT04' AS airport_icao_code, 'Primary code stored from source Other code: AT04. Source other code: AT04. Runway/surface: 10/28, 4,265 feet (1,300 m), Ice.' AS source_note, 'Wikipedia - List of airports in Antarctica' AS data_source_name
UNION ALL
SELECT 'AT05' AS airport_icao_code, 'Primary code stored from source Other code: AT05. Source other code: AT05. Runway/surface: 09/27, 9,345 feet (2,848 m), Ice.' AS source_note, 'Wikipedia - List of airports in Antarctica' AS data_source_name
UNION ALL
SELECT 'AT07' AS airport_icao_code, 'Primary code stored from source Other code: AT07. Source other code: AT07. Runway/surface: 17/35, 317 feet (97 m), Ice.' AS source_note, 'Wikipedia - List of airports in Antarctica' AS data_source_name
UNION ALL
SELECT 'AT09' AS airport_icao_code, 'Primary code stored from source Other code: AT09. Source other code: AT09. Runway/surface: 18/36, 2,376 feet (724 m), Ice.' AS source_note, 'Wikipedia - List of airports in Antarctica' AS data_source_name
UNION ALL
SELECT 'AT10' AS airport_icao_code, 'Primary code stored from source Other code: AT10. Source other code: AT10. Runway/surface: 17/35, 3,960 feet (1,210 m), Snow.' AS source_note, 'Wikipedia - List of airports in Antarctica' AS data_source_name
UNION ALL
SELECT 'EGAH' AS airport_icao_code, 'Source other code: AT11. Runway/surface: 09/27, 1,191 feet (363 m), Snow.' AS source_note, 'Wikipedia - List of airports in Antarctica' AS data_source_name
UNION ALL
SELECT 'NZSP' AS airport_icao_code, 'Runway/surface: 02/20, 12,000 feet (3,700 m), Snow.' AS source_note, 'Wikipedia - List of airports in Antarctica' AS data_source_name
UNION ALL
SELECT 'AT12' AS airport_icao_code, 'Primary code stored from source Other code: AT12. Source other code: AT12. Runway/surface: 17/35, 6,560 feet (2,000 m), Ice.' AS source_note, 'Wikipedia - List of airports in Antarctica' AS data_source_name
UNION ALL
SELECT 'SAWB' AS airport_icao_code, 'Runway/surface: 05/23, 4,134 feet (1,260 m), Gravel.' AS source_note, 'Wikipedia - List of airports in Antarctica' AS data_source_name
UNION ALL
SELECT 'SAWZ' AS airport_icao_code, 'Runway/surface: 4,920 feet (1,500 m), Sea Ice.' AS source_note, 'Wikipedia - List of airports in Antarctica' AS data_source_name
UNION ALL
SELECT 'NZIR' AS airport_icao_code, 'Runway/surface: 11/29, 9,979 feet (3,042 m), Ice; 16/34, 9,979 feet (3,042 m), Ice.' AS source_note, 'Wikipedia - List of airports in Antarctica' AS data_source_name
UNION ALL
SELECT 'AT14' AS airport_icao_code, 'Primary code stored from source Other code: AT14. Source other code: AT14. Runway/surface: 01/19, 3,960 feet (1,210 m), Ice.' AS source_note, 'Wikipedia - List of airports in Antarctica' AS data_source_name
UNION ALL
SELECT 'AT15' AS airport_icao_code, 'Primary code stored from source Other code: AT15. Source other code: AT15. Runway/surface: 10/28, 8,395 feet (2,559 m), Ice.' AS source_note, 'Wikipedia - List of airports in Antarctica' AS data_source_name
UNION ALL
SELECT 'AT16' AS airport_icao_code, 'Primary code stored from source Other code: AT16. Source other code: AT16. Runway/surface: 15/33, 3,326 feet (1,014 m), Ice.' AS source_note, 'Wikipedia - List of airports in Antarctica' AS data_source_name
UNION ALL
SELECT 'AT17' AS airport_icao_code, 'Primary code stored from source Other code: AT17. Source other code: AT17. Runway/surface: 10/28, 10,824 feet (3,299 m), Blue Ice.' AS source_note, 'Wikipedia - List of airports in Antarctica' AS data_source_name
UNION ALL
SELECT 'SCBO' AS airport_icao_code, 'Runway/surface: 2,625 feet (800 m), Ice.' AS source_note, 'Wikipedia - List of airports in Antarctica' AS data_source_name
UNION ALL
SELECT 'AT18' AS airport_icao_code, 'Primary code stored from source Other code: AT18. Source other code: AT18. Runway/surface: 18/36, 5,914 feet (1,803 m), Ice.' AS source_note, 'Wikipedia - List of airports in Antarctica' AS data_source_name
UNION ALL
SELECT 'NZ12' AS airport_icao_code, 'Source other code: NZ0B AG11180. Runway/surface: 01/19, 2,500 feet (760 m), Snow.' AS source_note, 'Wikipedia - List of airports in Antarctica' AS data_source_name
UNION ALL
SELECT 'SCPZ' AS airport_icao_code, 'Runway/surface: 24M, 3,281 feet (1,000 m), Ice.' AS source_note, 'Wikipedia - List of airports in Antarctica' AS data_source_name
UNION ALL
SELECT 'NZPG' AS airport_icao_code, 'Runway/surface: 15/33, 10,000 feet (3,000 m), Ice; 08/26, 10,000 feet (3,000 m), Ice skiway.' AS source_note, 'Wikipedia - List of airports in Antarctica' AS data_source_name
UNION ALL
SELECT 'SA47' AS airport_icao_code, 'Primary code stored from source Other code: SA47. Source other code: SA47. Runway/surface: 08/26, 3,485 feet (1,062 m), Ice.' AS source_note, 'Wikipedia - List of airports in Antarctica' AS data_source_name
UNION ALL
SELECT 'NZFX' AS airport_icao_code, 'Runway/surface: 15/33, 11,000 feet (3,400 m), Compacted Snow.' AS source_note, 'Wikipedia - List of airports in Antarctica' AS data_source_name
UNION ALL
SELECT 'AT20' AS airport_icao_code, 'Primary code stored from source Other code: AT20. Source other code: AT20. Runway/surface: 18/36, 11,458 feet (3,492 m), Ice.' AS source_note, 'Wikipedia - List of airports in Antarctica' AS data_source_name
UNION ALL
SELECT 'AT99' AS airport_icao_code, 'Primary code stored from source Other code: AT99. Source other code: AT99. Runway/surface: 4,650 feet (1,420 m), Blue Ice.' AS source_note, 'Wikipedia - List of airports in Antarctica' AS data_source_name
UNION ALL
SELECT 'SCRM' AS airport_icao_code, 'Runway/surface: 11/29, 4,232 feet (1,290 m), Gravel.' AS source_note, 'Wikipedia - List of airports in Antarctica' AS data_source_name
UNION ALL
SELECT 'EGAR' AS airport_icao_code, 'Source other code: AT01. Runway/surface: 18/36, 2,851 feet (869 m), Gravel.' AS source_note, 'Wikipedia - List of airports in Antarctica' AS data_source_name
UNION ALL
SELECT 'AT21' AS airport_icao_code, 'Primary code stored from source Other code: AT21. Source other code: AT21. Runway/surface: 17/35, 1,320 feet (400 m), Ice.' AS source_note, 'Wikipedia - List of airports in Antarctica' AS data_source_name
UNION ALL
SELECT 'SAYS' AS airport_icao_code, 'Runway/surface: 1,640 feet (500 m), Ice.' AS source_note, 'Wikipedia - List of airports in Antarctica' AS data_source_name
UNION ALL
SELECT 'AT22' AS airport_icao_code, 'Primary code stored from source Other code: AT22. Source other code: AT22. Runway/surface: 17/35, 3,274 feet (998 m), Ice.' AS source_note, 'Wikipedia - List of airports in Antarctica' AS data_source_name
UNION ALL
SELECT 'AT25' AS airport_icao_code, 'Primary code stored from source Other code: AT25. Source other code: AT25. Runway/surface: 17/35, 4,000 feet (1,200 m), Ice.' AS source_note, 'Wikipedia - List of airports in Antarctica' AS data_source_name
UNION ALL
SELECT 'AT23' AS airport_icao_code, 'Primary code stored from source Other code: AT23. Source other code: AT23. Runway/surface: 17/35, 3,274 feet (998 m), Ice.' AS source_note, 'Wikipedia - List of airports in Antarctica' AS data_source_name
UNION ALL
SELECT 'EGAT' AS airport_icao_code, 'Source other code: AT24. Runway/surface: 14/32, 3,960 feet (1,210 m), Blue Ice.' AS source_note, 'Wikipedia - List of airports in Antarctica' AS data_source_name
UNION ALL
SELECT 'AT26' AS airport_icao_code, 'Primary code stored from source Other code: AT26. Source other code: AT26. Runway/surface: 17/35, 5,175 feet (1,577 m), Ice.' AS source_note, 'Wikipedia - List of airports in Antarctica' AS data_source_name
UNION ALL
SELECT 'ENOE' AS airport_icao_code, 'Source other code: AT27. Runway/surface: 11/29, 10,826 feet (3,300 m), Blue ice.' AS source_note, 'Wikipedia - List of airports in Antarctica' AS data_source_name
UNION ALL
SELECT 'SCGC' AS airport_icao_code, 'Runway/surface: 18/36, 9,842 feet (3,000 m), Blue ice.' AS source_note, 'Wikipedia - List of airports in Antarctica' AS data_source_name
UNION ALL
SELECT 'AT28' AS airport_icao_code, 'Primary code stored from source Other code: AT28. Source other code: AT28. Runway/surface: 03/21, 11,983 feet (3,652 m), Ice.' AS source_note, 'Wikipedia - List of airports in Antarctica' AS data_source_name
UNION ALL
SELECT 'YWKS' AS airport_icao_code, 'Runway/surface: 09/27, 13,123 feet (4,000 m), Ice.' AS source_note, 'Wikipedia - List of airports in Antarctica' AS data_source_name
UNION ALL
SELECT 'NZWD' AS airport_icao_code, 'Runway/surface: 07/25, 10,000 feet (3,000 m), Snow; 15/33, 10,000 feet (3,000 m), Snow.' AS source_note, 'Wikipedia - List of airports in Antarctica' AS data_source_name
UNION ALL
SELECT 'AT98' AS airport_icao_code, 'Primary code stored from source Other code: AT98. Source other code: AT98. Runway/surface: 2,500 metres (8,200 ft), Blue Ice.' AS source_note, 'Wikipedia - List of airports in Antarctica' AS data_source_name
UNION ALL
SELECT 'NZTB' AS airport_icao_code, 'Source other code: AT13. Runway/surface: 03/21, 10,137 feet (3,090 m), Ice.' AS source_note, 'Wikipedia - List of airports in Antarctica' AS data_source_name
UNION ALL
SELECT 'SAYO' AS airport_icao_code, 'Runway/surface: Surface not specified in table.' AS source_note, 'Wikipedia - List of airports in Antarctica' AS data_source_name
) s
JOIN airports a
  ON a.icao_code = s.airport_icao_code
ON DUPLICATE KEY UPDATE
  source_note = VALUES(source_note),
  data_source_name = VALUES(data_source_name);

-- Diagnostics: missing Antarctica country row.
SELECT
  t.country_name,
  COUNT(*) AS rows_not_imported_missing_country
FROM tmp_antarctica_airports t
LEFT JOIN countries c
  ON c.name = t.country_name
 AND c.world_region_code = 'ANTARCTICA'
WHERE c.id IS NULL
GROUP BY t.country_name;

-- Verification.
SELECT COUNT(*) AS total_airports
FROM airports;

SELECT
  c.name AS country_name,
  COUNT(*) AS total_airports,
  SUM(CASE WHEN a.latitude IS NOT NULL AND a.longitude IS NOT NULL THEN 1 ELSE 0 END) AS airports_with_coordinates,
  SUM(CASE WHEN a.airport_type = 'AIRFIELD' THEN 1 ELSE 0 END) AS heliports,
  SUM(CASE WHEN a.airport_type IN ('AIRFIELD', 'AIRSTRIP') THEN 1 ELSE 0 END) AS airfields_or_airstrips
FROM airports a
JOIN countries c
  ON c.id = a.country_id
WHERE c.name = 'Antarctica'
  AND c.world_region_code = 'ANTARCTICA'
GROUP BY c.name;
