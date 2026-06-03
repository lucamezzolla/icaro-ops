-- West Africa 3 airport seed batch.
-- Countries:
-- Nigeria, Senegal, Sierra Leone, Togo.
-- Robust import: uses a temporary table and JOINs to countries / prefixes.

USE icaro_ops;

CREATE TEMPORARY TABLE tmp_west_africa_3_airports (
  country_name VARCHAR(120) NOT NULL,
  icao_prefix VARCHAR(8) NOT NULL,
  icao_code CHAR(4) NOT NULL,
  iata_code CHAR(3) NULL,
  name VARCHAR(180) NOT NULL,
  city VARCHAR(120) NULL,
  subdivision_name VARCHAR(120) NULL,
  latitude DECIMAL(10,7) NULL,
  longitude DECIMAL(10,7) NULL,
  airport_type VARCHAR(40) NOT NULL,
  service_category VARCHAR(40) NOT NULL,
  is_closed BOOLEAN NOT NULL DEFAULT FALSE,
  data_source_name VARCHAR(120) NULL,
  data_source_url VARCHAR(255) NULL,

  PRIMARY KEY (icao_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO tmp_west_africa_3_airports (
  country_name,
  icao_prefix,
  icao_code,
  iata_code,
  name,
  city,
  subdivision_name,
  latitude,
  longitude,
  airport_type,
  service_category,
  is_closed,
  data_source_name,
  data_source_url
) VALUES
('Nigeria', 'DN', 'DNAA', 'ABV', 'Nnamdi Azikiwe International Airport', 'Abuja', 'Federal Capital Territory', NULL, NULL, 'AIRPORT', 'INTERNATIONAL', FALSE, 'Wikipedia - List of airports in Nigeria', 'https://en.wikipedia.org/wiki/List_of_airports_in_Nigeria'),
('Nigeria', 'DN', 'DNAI', 'QUO', 'Victor Attah International Airport', 'Uyo', 'Akwa Ibom', NULL, NULL, 'AIRPORT', 'INTERNATIONAL', FALSE, 'Wikipedia - List of airports in Nigeria', 'https://en.wikipedia.org/wiki/List_of_airports_in_Nigeria'),
('Nigeria', 'DN', 'DNAN', 'ANA', 'Chinua Achebe International Airport', 'Anambra', 'Anambra', NULL, NULL, 'AIRPORT', 'INTERNATIONAL', FALSE, 'Wikipedia - List of airports in Nigeria', 'https://en.wikipedia.org/wiki/List_of_airports_in_Nigeria'),
('Nigeria', 'DN', 'DNCA', 'CBQ', 'Margaret Ekpo International Airport', 'Calabar', 'Cross River', NULL, NULL, 'AIRPORT', 'INTERNATIONAL', FALSE, 'Wikipedia - List of airports in Nigeria', 'https://en.wikipedia.org/wiki/List_of_airports_in_Nigeria'),
('Nigeria', 'DN', 'DNEB', NULL, 'Ebonyi State International Airport', 'Ebonyi', 'Ebonyi', NULL, NULL, 'AIRPORT', 'INTERNATIONAL', FALSE, 'Wikipedia - List of airports in Nigeria', 'https://en.wikipedia.org/wiki/List_of_airports_in_Nigeria'),
('Nigeria', 'DN', 'DNEN', 'ENU', 'Akanu Ibiam International Airport', 'Enugu', 'Enugu', NULL, NULL, 'AIRPORT', 'INTERNATIONAL', FALSE, 'Wikipedia - List of airports in Nigeria', 'https://en.wikipedia.org/wiki/List_of_airports_in_Nigeria'),
('Nigeria', 'DN', 'DNIL', 'ILR', 'General Tunde Idiagbon International Airport', 'Ilorin', 'Kwara', NULL, NULL, 'AIRPORT', 'INTERNATIONAL', FALSE, 'Wikipedia - List of airports in Nigeria', 'https://en.wikipedia.org/wiki/List_of_airports_in_Nigeria'),
('Nigeria', 'DN', 'DNKA', 'KAD', 'Kaduna International Airport', 'Kaduna', 'Kaduna', NULL, NULL, 'AIRPORT', 'INTERNATIONAL', FALSE, 'Wikipedia - List of airports in Nigeria', 'https://en.wikipedia.org/wiki/List_of_airports_in_Nigeria'),
('Nigeria', 'DN', 'DNKN', 'KAN', 'Mallam Aminu Kano International Airport', 'Kano', 'Kano', NULL, NULL, 'AIRPORT', 'INTERNATIONAL', FALSE, 'Wikipedia - List of airports in Nigeria', 'https://en.wikipedia.org/wiki/List_of_airports_in_Nigeria'),
('Nigeria', 'DN', 'DNMM', 'LOS', 'Murtala Muhammed International Airport', 'Lagos', 'Lagos', NULL, NULL, 'AIRPORT', 'INTERNATIONAL', FALSE, 'Wikipedia - List of airports in Nigeria', 'https://en.wikipedia.org/wiki/List_of_airports_in_Nigeria'),
('Nigeria', 'DN', 'DNPO', 'PHC', 'Port Harcourt International Airport', 'Port Harcourt', 'Rivers', NULL, NULL, 'AIRPORT', 'INTERNATIONAL', FALSE, 'Wikipedia - List of airports in Nigeria', 'https://en.wikipedia.org/wiki/List_of_airports_in_Nigeria'),
('Nigeria', 'DN', 'DNGA', 'GWI', 'Gateway International Airport', 'Iperu-Remo', 'Ogun', NULL, NULL, 'AIRPORT', 'INTERNATIONAL', FALSE, 'Wikipedia - List of airports in Nigeria', 'https://en.wikipedia.org/wiki/List_of_airports_in_Nigeria'),
('Nigeria', 'DN', 'DNSO', 'SKO', 'Sadiq Abubakar III International Airport', 'Sokoto', 'Sokoto', NULL, NULL, 'AIRPORT', 'INTERNATIONAL', FALSE, 'Wikipedia - List of airports in Nigeria', 'https://en.wikipedia.org/wiki/List_of_airports_in_Nigeria'),
('Nigeria', 'DN', 'DNAS', 'ABB', 'Asaba International Airport', 'Asaba', 'Delta', NULL, NULL, 'AIRPORT', 'INTERNATIONAL', FALSE, 'Wikipedia - List of airports in Nigeria', 'https://en.wikipedia.org/wiki/List_of_airports_in_Nigeria'),
('Nigeria', 'DN', 'DNBC', 'BCU', 'Sir Abubakar Tafawa Balewa Airport', 'Bauchi', 'Bauchi', NULL, NULL, 'AIRPORT', 'NATIONAL', FALSE, 'Wikipedia - List of airports in Nigeria', 'https://en.wikipedia.org/wiki/List_of_airports_in_Nigeria'),
('Nigeria', 'DN', 'DNBE', 'BNI', 'Benin Airport', 'Benin', 'Edo', NULL, NULL, 'AIRPORT', 'NATIONAL', FALSE, 'Wikipedia - List of airports in Nigeria', 'https://en.wikipedia.org/wiki/List_of_airports_in_Nigeria'),
('Nigeria', 'DN', 'DNIB', 'IBA', 'Ibadan Airport', 'Ibadan', 'Oyo', NULL, NULL, 'AIRPORT', 'NATIONAL', FALSE, 'Wikipedia - List of airports in Nigeria', 'https://en.wikipedia.org/wiki/List_of_airports_in_Nigeria'),
('Nigeria', 'DN', 'DNJO', 'JOS', 'Yakubu Gowon Airport', 'Jos', 'Plateau', NULL, NULL, 'AIRPORT', 'NATIONAL', FALSE, 'Wikipedia - List of airports in Nigeria', 'https://en.wikipedia.org/wiki/List_of_airports_in_Nigeria'),
('Nigeria', 'DN', 'DNMA', 'MIU', 'Maiduguri International Airport', 'Maiduguri', 'Borno', NULL, NULL, 'AIRPORT', 'INTERNATIONAL', FALSE, 'Wikipedia - List of airports in Nigeria', 'https://en.wikipedia.org/wiki/List_of_airports_in_Nigeria'),
('Nigeria', 'DN', 'DNIM', 'QOW', 'Sam Mbakwe International Cargo Airport', 'Owerri', 'Imo', NULL, NULL, 'AIRPORT', 'INTERNATIONAL', FALSE, 'Wikipedia - List of airports in Nigeria', 'https://en.wikipedia.org/wiki/List_of_airports_in_Nigeria'),
('Nigeria', 'DN', 'DNYO', 'YOL', 'Yola Airport', 'Yola', 'Adamawa', NULL, NULL, 'AIRPORT', 'NATIONAL', FALSE, 'Wikipedia - List of airports in Nigeria', 'https://en.wikipedia.org/wiki/List_of_airports_in_Nigeria'),
('Nigeria', 'DN', 'DNAK', 'AKR', 'Akure Airport', 'Akure', 'Ondo', NULL, NULL, 'AIRPORT', 'NATIONAL', FALSE, 'Wikipedia - List of airports in Nigeria', 'https://en.wikipedia.org/wiki/List_of_airports_in_Nigeria'),
('Nigeria', 'DN', 'DNGO', 'GMO', 'Gombe Lawanti International Airport', 'Gombe', 'Gombe', NULL, NULL, 'AIRPORT', 'INTERNATIONAL', FALSE, 'Wikipedia - List of airports in Nigeria', 'https://en.wikipedia.org/wiki/List_of_airports_in_Nigeria'),
('Nigeria', 'DN', 'DNBK', NULL, 'Kebbi International Airport', 'Birnin Kebbi', 'Kebbi', NULL, NULL, 'AIRPORT', 'INTERNATIONAL', FALSE, 'Wikipedia - List of airports in Nigeria', 'https://en.wikipedia.org/wiki/List_of_airports_in_Nigeria'),
('Nigeria', 'DN', 'DNDS', NULL, 'Dutse International Airport', 'Dutse', 'Jigawa', NULL, NULL, 'AIRPORT', 'INTERNATIONAL', FALSE, 'Wikipedia - List of airports in Nigeria', 'https://en.wikipedia.org/wiki/List_of_airports_in_Nigeria'),
('Nigeria', 'DN', 'DNJA', NULL, 'Jalingo Airport', 'Jalingo', 'Taraba', NULL, NULL, 'AIRPORT', 'NATIONAL', FALSE, 'Wikipedia - List of airports in Nigeria', 'https://en.wikipedia.org/wiki/List_of_airports_in_Nigeria'),
('Nigeria', 'DN', 'DNKT', 'DKA', 'Katsina Airport', 'Katsina', 'Katsina', NULL, NULL, 'AIRPORT', 'NATIONAL', FALSE, 'Wikipedia - List of airports in Nigeria', 'https://en.wikipedia.org/wiki/List_of_airports_in_Nigeria'),
('Nigeria', 'DN', 'DNMK', 'MDI', 'Makurdi Airport', 'Makurdi', 'Benue', NULL, NULL, 'AIRPORT', 'NATIONAL', FALSE, 'Wikipedia - List of airports in Nigeria', 'https://en.wikipedia.org/wiki/List_of_airports_in_Nigeria'),
('Nigeria', 'DN', 'DNMN', 'MXJ', 'Minna Airport', 'Minna', 'Niger', NULL, NULL, 'AIRPORT', 'NATIONAL', FALSE, 'Wikipedia - List of airports in Nigeria', 'https://en.wikipedia.org/wiki/List_of_airports_in_Nigeria'),
('Nigeria', 'DN', 'DNSU', 'QRW', 'Osubi Airport', 'Warri', 'Delta', NULL, NULL, 'AIRPORT', 'NATIONAL', FALSE, 'Wikipedia - List of airports in Nigeria', 'https://en.wikipedia.org/wiki/List_of_airports_in_Nigeria'),
('Nigeria', 'DN', 'DNZA', 'ZAR', 'Zaria Airport', 'Zaria', 'Kaduna', NULL, NULL, 'AIRPORT', 'NATIONAL', FALSE, 'Wikipedia - List of airports in Nigeria', 'https://en.wikipedia.org/wiki/List_of_airports_in_Nigeria'),
('Nigeria', 'DN', 'DN51', NULL, 'Ajaokuta Airstrip', 'Ajaokuta', 'Kogi', NULL, NULL, 'AIRSTRIP', 'NATIONAL', FALSE, 'Wikipedia - List of airports in Nigeria', 'https://en.wikipedia.org/wiki/List_of_airports_in_Nigeria'),
('Nigeria', 'DN', 'DN54', NULL, 'Bajoga Northeast Airport', 'Bajoga', 'Gombe', NULL, NULL, 'AIRPORT', 'NATIONAL', FALSE, 'Wikipedia - List of airports in Nigeria', 'https://en.wikipedia.org/wiki/List_of_airports_in_Nigeria'),
('Nigeria', 'DN', 'DNBI', NULL, 'Bida Airstrip', 'Bida', 'Niger', NULL, NULL, 'AIRSTRIP', 'NATIONAL', FALSE, 'Wikipedia - List of airports in Nigeria', 'https://en.wikipedia.org/wiki/List_of_airports_in_Nigeria'),
('Nigeria', 'DN', 'DNEK', NULL, 'Eket Airstrip', 'Eket', 'Akwa Ibom', NULL, NULL, 'AIRSTRIP', 'NATIONAL', FALSE, 'Wikipedia - List of airports in Nigeria', 'https://en.wikipedia.org/wiki/List_of_airports_in_Nigeria'),
('Nigeria', 'DN', 'DN56', NULL, 'Escravos Airstrip', 'Escravos', 'Delta', NULL, NULL, 'AIRSTRIP', 'NATIONAL', FALSE, 'Wikipedia - List of airports in Nigeria', 'https://en.wikipedia.org/wiki/List_of_airports_in_Nigeria'),
('Nigeria', 'DN', 'DNGU', 'QUS', 'Gusau Airstrip', 'Gusau', 'Zamfara', NULL, NULL, 'AIRSTRIP', 'NATIONAL', FALSE, 'Wikipedia - List of airports in Nigeria', 'https://en.wikipedia.org/wiki/List_of_airports_in_Nigeria'),
('Nigeria', 'DN', 'DN50', NULL, 'Shiroro Airstrip', 'Shiroro', 'Niger', NULL, NULL, 'AIRSTRIP', 'NATIONAL', FALSE, 'Wikipedia - List of airports in Nigeria', 'https://en.wikipedia.org/wiki/List_of_airports_in_Nigeria'),
('Nigeria', 'DN', 'DN57', NULL, 'Katsina Air Force Base', 'Katsina', 'Katsina', NULL, NULL, 'AIRFIELD', 'MILITARY', FALSE, 'Wikipedia - List of airports in Nigeria', 'https://en.wikipedia.org/wiki/List_of_airports_in_Nigeria'),
('Nigeria', 'DN', 'DNPM', 'PHG', 'Port Harcourt NAF Base', 'Port Harcourt', 'Rivers', NULL, NULL, 'AIRFIELD', 'MILITARY', FALSE, 'Wikipedia - List of airports in Nigeria', 'https://en.wikipedia.org/wiki/List_of_airports_in_Nigeria'),
('Nigeria', 'DN', 'DN53', NULL, 'Kaduna Air Force Base', 'Kaduna', 'Kaduna', NULL, NULL, 'AIRFIELD', 'MILITARY', FALSE, 'Wikipedia - List of airports in Nigeria', 'https://en.wikipedia.org/wiki/List_of_airports_in_Nigeria'),
('Senegal', 'GO', 'GOTB', 'BXE', 'Bakel Airport', 'Bakel', 'Tambacounda', 14.8472222, -12.4680556, 'AIRPORT', 'NATIONAL', FALSE, 'Wikipedia - List of airports in Senegal', 'https://en.wikipedia.org/wiki/List_of_airports_in_Senegal'),
('Senegal', 'GO', 'GOGS', 'CSK', 'Cap Skirring Airport', 'Cap Skirring', 'Ziguinchor', 12.41, -16.7461111, 'AIRPORT', 'NATIONAL', FALSE, 'Wikipedia - List of airports in Senegal', 'https://en.wikipedia.org/wiki/List_of_airports_in_Senegal'),
('Senegal', 'GO', 'GOOY', 'DKR', 'Léopold Sédar Senghor International Airport', 'Dakar', 'Dakar', 14.7394444, -17.49, 'AIRPORT', 'INTERNATIONAL', FALSE, 'Wikipedia - List of airports in Senegal', 'https://en.wikipedia.org/wiki/List_of_airports_in_Senegal'),
('Senegal', 'GO', 'GOBD', 'DSS', 'Blaise Diagne International Airport', 'Dakar', 'Thiès', 14.6711111, -17.0669444, 'AIRPORT', 'INTERNATIONAL', FALSE, 'Wikipedia - List of airports in Senegal', 'https://en.wikipedia.org/wiki/List_of_airports_in_Senegal'),
('Senegal', 'GO', 'GO66', NULL, 'Dodji Airport', 'Dodji', 'Louga', 15.5438889, -14.9583333, 'AIRPORT', 'NATIONAL', FALSE, 'Wikipedia - List of airports in Senegal', 'https://en.wikipedia.org/wiki/List_of_airports_in_Senegal'),
('Senegal', 'GO', 'GOOK', 'KLC', 'Kaolack Airport', 'Kaolack', 'Kaolack', 14.1466667, -16.0511111, 'AIRPORT', 'NATIONAL', FALSE, 'Wikipedia - List of airports in Senegal', 'https://en.wikipedia.org/wiki/List_of_airports_in_Senegal'),
('Senegal', 'GO', 'GOTK', 'KGG', 'Kédougou Airport', 'Kédougou', 'Kédougou', 12.5722222, -12.2202778, 'AIRPORT', 'NATIONAL', FALSE, 'Wikipedia - List of airports in Senegal', 'https://en.wikipedia.org/wiki/List_of_airports_in_Senegal'),
('Senegal', 'GO', 'GODK', 'KDA', 'Kolda North Airport', 'Kolda', 'Kolda', 12.8983333, -14.9680556, 'AIRPORT', 'NATIONAL', FALSE, 'Wikipedia - List of airports in Senegal', 'https://en.wikipedia.org/wiki/List_of_airports_in_Senegal'),
('Senegal', 'GO', 'GOOG', NULL, 'Linguère Airport', 'Linguère', 'Louga', 15.4, -15.0838889, 'AIRPORT', 'NATIONAL', FALSE, 'Wikipedia - List of airports in Senegal', 'https://en.wikipedia.org/wiki/List_of_airports_in_Senegal'),
('Senegal', 'GO', 'GOSM', 'MAX', 'Ouro Sogui Airport', 'Matam', 'Matam', 15.5936111, -13.3227778, 'AIRPORT', 'NATIONAL', FALSE, 'Wikipedia - List of airports in Senegal', 'https://en.wikipedia.org/wiki/List_of_airports_in_Senegal'),
('Senegal', 'GO', 'GOTN', 'NIK', 'Niokolo-Koba Airport', 'Niokolo-Koba', 'Niokolo-Koba National Park', 13.0525, -12.7272222, 'AIRPORT', 'NATIONAL', FALSE, 'Wikipedia - List of airports in Senegal', 'https://en.wikipedia.org/wiki/List_of_airports_in_Senegal'),
('Senegal', 'GO', 'GOSP', 'POD', 'Podor Airport', 'Podor', 'Saint-Louis', 16.6780556, -14.965, 'AIRPORT', 'NATIONAL', FALSE, 'Wikipedia - List of airports in Senegal', 'https://en.wikipedia.org/wiki/List_of_airports_in_Senegal'),
('Senegal', 'GO', 'GOSR', 'RDT', 'Richard Toll Airport', 'Richard Toll', 'Saint-Louis', 16.4375, -15.6572222, 'AIRPORT', 'NATIONAL', FALSE, 'Wikipedia - List of airports in Senegal', 'https://en.wikipedia.org/wiki/List_of_airports_in_Senegal'),
('Senegal', 'GO', 'GOSS', 'XLS', 'Saint-Louis Airport', 'Saint-Louis', 'Saint-Louis', 16.0508333, -16.4630556, 'AIRPORT', 'NATIONAL', FALSE, 'Wikipedia - List of airports in Senegal', 'https://en.wikipedia.org/wiki/List_of_airports_in_Senegal'),
('Senegal', 'GO', 'GOTS', 'SMY', 'Simenti Airport', 'Simenti', 'Tambacounda', 13.0466667, -13.2947222, 'AIRPORT', 'NATIONAL', FALSE, 'Wikipedia - List of airports in Senegal', 'https://en.wikipedia.org/wiki/List_of_airports_in_Senegal'),
('Senegal', 'GO', 'GOTT', 'TUD', 'Tambacounda Airport', 'Tambacounda', 'Tambacounda', 13.7366667, -13.6530556, 'AIRPORT', 'NATIONAL', FALSE, 'Wikipedia - List of airports in Senegal', 'https://en.wikipedia.org/wiki/List_of_airports_in_Senegal'),
('Senegal', 'GO', 'GOGG', 'ZIG', 'Ziguinchor Airport', 'Ziguinchor', 'Ziguinchor', 12.5555556, -16.2816667, 'AIRPORT', 'NATIONAL', FALSE, 'Wikipedia - List of airports in Senegal', 'https://en.wikipedia.org/wiki/List_of_airports_in_Senegal'),
('Senegal', 'GO', 'GOOD', NULL, 'Diourbel Airport', 'Diourbel', 'Diourbel', 14.6527778, -16.1866667, 'AIRPORT', 'NATIONAL', TRUE, 'Wikipedia - List of airports in Senegal', 'https://en.wikipedia.org/wiki/List_of_airports_in_Senegal'),
('Senegal', 'GO', 'GOGK', NULL, 'Kolda Airport', 'Kolda', 'Kolda', 12.8797222, -14.9561111, 'AIRPORT', 'NATIONAL', TRUE, 'Wikipedia - List of airports in Senegal', 'https://en.wikipedia.org/wiki/List_of_airports_in_Senegal'),
('Sierra Leone', 'GF', 'GFBO', 'KBS', 'Bo Airport', 'Bo', NULL, NULL, NULL, 'AIRPORT', 'NATIONAL', FALSE, 'Wikipedia - List of airports in Sierra Leone', 'https://en.wikipedia.org/wiki/List_of_airports_in_Sierra_Leone'),
('Sierra Leone', 'GF', 'GFBN', 'BTE', 'Sherbro International Airport', 'Sherbro, Bonthe', NULL, NULL, NULL, 'AIRPORT', 'INTERNATIONAL', FALSE, 'Wikipedia - List of airports in Sierra Leone', 'https://en.wikipedia.org/wiki/List_of_airports_in_Sierra_Leone'),
('Sierra Leone', 'GF', 'GFHA', 'HGS', 'Hastings Airport', 'Freetown', NULL, NULL, NULL, 'AIRPORT', 'NATIONAL', FALSE, 'Wikipedia - List of airports in Sierra Leone', 'https://en.wikipedia.org/wiki/List_of_airports_in_Sierra_Leone'),
('Sierra Leone', 'GF', 'GFLL', 'FNA', 'Freetown International Airport', 'Freetown', NULL, NULL, NULL, 'AIRPORT', 'INTERNATIONAL', FALSE, 'Wikipedia - List of airports in Sierra Leone', 'https://en.wikipedia.org/wiki/List_of_airports_in_Sierra_Leone'),
('Sierra Leone', 'GF', 'GFGK', 'GBK', 'Gbangbatok Airport', 'Gbangbatok', NULL, NULL, NULL, 'AIRPORT', 'NATIONAL', FALSE, 'Wikipedia - List of airports in Sierra Leone', 'https://en.wikipedia.org/wiki/List_of_airports_in_Sierra_Leone'),
('Sierra Leone', 'GF', 'GFKB', 'KBA', 'Kabala Airport', 'Kabala', NULL, NULL, NULL, 'AIRPORT', 'NATIONAL', FALSE, 'Wikipedia - List of airports in Sierra Leone', 'https://en.wikipedia.org/wiki/List_of_airports_in_Sierra_Leone'),
('Sierra Leone', 'GF', 'GFKE', 'KEN', 'Kenema Airport', 'Kenema', NULL, NULL, NULL, 'AIRPORT', 'NATIONAL', FALSE, 'Wikipedia - List of airports in Sierra Leone', 'https://en.wikipedia.org/wiki/List_of_airports_in_Sierra_Leone'),
('Sierra Leone', 'GF', 'GFYE', 'WYE', 'Yengema Airport', 'Yengema', NULL, NULL, NULL, 'AIRPORT', 'NATIONAL', FALSE, 'Wikipedia - List of airports in Sierra Leone', 'https://en.wikipedia.org/wiki/List_of_airports_in_Sierra_Leone'),
('Togo', 'DX', 'DXKP', NULL, 'Kolokope Airport', 'Anié', 'Plateaux', NULL, NULL, 'AIRPORT', 'NATIONAL', FALSE, 'Wikipedia - List of airports in Togo', 'https://en.wikipedia.org/wiki/List_of_airports_in_Togo'),
('Togo', 'DX', 'DXAK', NULL, 'Akpaka Airport', 'Atakpamé', 'Plateaux', NULL, NULL, 'AIRPORT', 'NATIONAL', FALSE, 'Wikipedia - List of airports in Togo', 'https://en.wikipedia.org/wiki/List_of_airports_in_Togo'),
('Togo', 'DX', 'DXDP', NULL, 'Djangou Airport', 'Dapaong', 'Savanes', NULL, NULL, 'AIRPORT', 'NATIONAL', FALSE, 'Wikipedia - List of airports in Togo', 'https://en.wikipedia.org/wiki/List_of_airports_in_Togo'),
('Togo', 'DX', 'DXXX', 'LFW', 'Lomé-Tokoin International Airport', 'Lomé', 'Maritime', NULL, NULL, 'AIRPORT', 'INTERNATIONAL', FALSE, 'Wikipedia - List of airports in Togo', 'https://en.wikipedia.org/wiki/List_of_airports_in_Togo'),
('Togo', 'DX', 'DXNG', 'LRL', 'Niamtougou International Airport', 'Niamtougou', 'Kara', NULL, NULL, 'AIRPORT', 'INTERNATIONAL', FALSE, 'Wikipedia - List of airports in Togo', 'https://en.wikipedia.org/wiki/List_of_airports_in_Togo'),
('Togo', 'DX', 'DXMG', NULL, 'Sansanné-Mango Airport', 'Sansanné-Mango', 'Savanes', NULL, NULL, 'AIRPORT', 'NATIONAL', FALSE, 'Wikipedia - List of airports in Togo', 'https://en.wikipedia.org/wiki/List_of_airports_in_Togo'),
('Togo', 'DX', 'DXSK', NULL, 'Sokodé Airport', 'Sokodé', 'Centrale', NULL, NULL, 'AIRPORT', 'NATIONAL', FALSE, 'Wikipedia - List of airports in Togo', 'https://en.wikipedia.org/wiki/List_of_airports_in_Togo')
ON DUPLICATE KEY UPDATE
  country_name = VALUES(country_name),
  icao_prefix = VALUES(icao_prefix),
  iata_code = VALUES(iata_code),
  name = VALUES(name),
  city = VALUES(city),
  subdivision_name = VALUES(subdivision_name),
  latitude = VALUES(latitude),
  longitude = VALUES(longitude),
  airport_type = VALUES(airport_type),
  service_category = VALUES(service_category),
  is_closed = VALUES(is_closed),
  data_source_name = VALUES(data_source_name),
  data_source_url = VALUES(data_source_url);

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
  'ICAO prefix for airport imports.'
FROM tmp_west_africa_3_airports t
JOIN countries c
  ON c.name = t.country_name
 AND c.world_region_code = 'AFRICA'
ON DUPLICATE KEY UPDATE
  country_id = VALUES(country_id),
  area_name = VALUES(area_name),
  notes = VALUES(notes),
  is_active = TRUE;

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
  NULL,
  t.subdivision_name,
  t.latitude,
  t.longitude,
  NULL,
  t.airport_type,
  t.service_category,
  TRUE,
  CASE WHEN t.service_category IN ('INTERNATIONAL', 'NATIONAL') THEN TRUE ELSE FALSE END,
  CASE WHEN t.service_category = 'MILITARY' THEN TRUE ELSE FALSE END,
  t.is_closed,
  NULL,
  NULL,
  NULL,
  NULL,
  t.data_source_name,
  t.data_source_url,
  'PARTIAL'
FROM tmp_west_africa_3_airports t
JOIN countries c
  ON c.name = t.country_name
 AND c.world_region_code = 'AFRICA'
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

-- Diagnostics: missing countries.
SELECT
  t.country_name,
  COUNT(*) AS rows_not_imported_missing_country
FROM tmp_west_africa_3_airports t
LEFT JOIN countries c
  ON c.name = t.country_name
 AND c.world_region_code = 'AFRICA'
WHERE c.id IS NULL
GROUP BY t.country_name
ORDER BY t.country_name;

-- Verification.
SELECT COUNT(*) AS total_airports
FROM airports;

SELECT
  c.name AS country_name,
  COUNT(*) AS total_airports,
  SUM(CASE WHEN a.latitude IS NOT NULL AND a.longitude IS NOT NULL THEN 1 ELSE 0 END) AS airports_with_coordinates,
  SUM(CASE WHEN a.elevation_ft IS NOT NULL THEN 1 ELSE 0 END) AS airports_with_elevation,
  SUM(CASE WHEN a.is_closed THEN 1 ELSE 0 END) AS closed_airports
FROM airports a
JOIN countries c
  ON c.id = a.country_id
WHERE c.name IN ('Nigeria', 'Senegal', 'Sierra Leone', 'Togo')
  AND c.world_region_code = 'AFRICA'
GROUP BY c.name
ORDER BY c.name;
