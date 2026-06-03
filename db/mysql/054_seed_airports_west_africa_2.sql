-- West Africa 2 airport seed batch.
-- Countries:
-- Guinea, Guinea-Bissau, Liberia, Mali, Mauritania, Niger.
-- Robust import: uses a temporary table and JOINs to countries / prefixes to avoid NULL country_id failures.

USE icaro_ops;

CREATE TEMPORARY TABLE tmp_west_africa_2_airports (
  country_name VARCHAR(120) NOT NULL,
  icao_prefix VARCHAR(8) NOT NULL,
  icao_code CHAR(4) NOT NULL,
  iata_code CHAR(3) NULL,
  name VARCHAR(160) NOT NULL,
  city VARCHAR(120) NULL,
  raw_coordinates VARCHAR(80) NULL,
  elevation_ft INT NULL,
  airport_type VARCHAR(40) NOT NULL,
  service_category VARCHAR(40) NOT NULL,
  is_closed BOOLEAN NOT NULL DEFAULT FALSE,
  data_source_name VARCHAR(120) NULL,
  data_source_url VARCHAR(255) NULL,

  PRIMARY KEY (icao_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO tmp_west_africa_2_airports (
  country_name,
  icao_prefix,
  icao_code,
  iata_code,
  name,
  city,
  raw_coordinates,
  elevation_ft,
  airport_type,
  service_category,
  is_closed,
  data_source_name,
  data_source_url
) VALUES
('Guinea', 'GU', 'GUGO', NULL, 'Gbenko Airport', 'Banankoro', NULL, NULL, 'AIRPORT', 'NATIONAL', FALSE, 'Wikipedia - List of airports in Guinea', 'https://en.wikipedia.org/wiki/List_of_airports_in_Guinea'),
('Guinea', 'GU', 'GUBE', NULL, 'Beyla Airport', 'Beyla', NULL, NULL, 'AIRPORT', 'NATIONAL', FALSE, 'Wikipedia - List of airports in Guinea', 'https://en.wikipedia.org/wiki/List_of_airports_in_Guinea'),
('Guinea', 'GU', 'GUOK', 'BKJ', 'Boké Baralande Airport', 'Boké', NULL, NULL, 'AIRPORT', 'NATIONAL', FALSE, 'Wikipedia - List of airports in Guinea', 'https://en.wikipedia.org/wiki/List_of_airports_in_Guinea'),
('Guinea', 'GU', 'GUCY', 'CKY', 'Conakry International Airport (Gbessia Int''l)', 'Conakry', NULL, NULL, 'AIRPORT', 'INTERNATIONAL', FALSE, 'Wikipedia - List of airports in Guinea', 'https://en.wikipedia.org/wiki/List_of_airports_in_Guinea'),
('Guinea', 'GU', 'GUFH', 'FAA', 'Faranah Airport', 'Faranah', NULL, NULL, 'AIRPORT', 'NATIONAL', FALSE, 'Wikipedia - List of airports in Guinea', 'https://en.wikipedia.org/wiki/List_of_airports_in_Guinea'),
('Guinea', 'GU', 'GUFA', 'FIG', 'Fria Airport', 'Fria', NULL, NULL, 'AIRPORT', 'NATIONAL', FALSE, 'Wikipedia - List of airports in Guinea', 'https://en.wikipedia.org/wiki/List_of_airports_in_Guinea'),
('Guinea', 'GU', 'GUKR', NULL, 'Kawass Airport', 'Port Kamsar', NULL, NULL, 'AIRPORT', 'NATIONAL', FALSE, 'Wikipedia - List of airports in Guinea', 'https://en.wikipedia.org/wiki/List_of_airports_in_Guinea'),
('Guinea', 'GU', 'GUXD', 'KNN', 'Kankan Airport', 'Kankan', NULL, NULL, 'AIRPORT', 'NATIONAL', FALSE, 'Wikipedia - List of airports in Guinea', 'https://en.wikipedia.org/wiki/List_of_airports_in_Guinea'),
('Guinea', 'GU', 'GUKU', 'KSI', 'Kissidougou Airport', 'Kissidougou', NULL, NULL, 'AIRPORT', 'NATIONAL', FALSE, 'Wikipedia - List of airports in Guinea', 'https://en.wikipedia.org/wiki/List_of_airports_in_Guinea'),
('Guinea', 'GU', 'GUSB', 'SBI', 'Sambailo Airport', 'Koundara', NULL, NULL, 'AIRPORT', 'NATIONAL', FALSE, 'Wikipedia - List of airports in Guinea', 'https://en.wikipedia.org/wiki/List_of_airports_in_Guinea'),
('Guinea', 'GU', 'GULB', 'LEK', 'Tata Airport', 'Labe', NULL, NULL, 'AIRPORT', 'NATIONAL', FALSE, 'Wikipedia - List of airports in Guinea', 'https://en.wikipedia.org/wiki/List_of_airports_in_Guinea'),
('Guinea', 'GU', 'GUMA', 'MCA', 'Macenta Airport', 'Macenta', NULL, NULL, 'AIRPORT', 'NATIONAL', FALSE, 'Wikipedia - List of airports in Guinea', 'https://en.wikipedia.org/wiki/List_of_airports_in_Guinea'),
('Guinea', 'GU', 'GUNZ', 'NZE', 'Nzérékoré Airport', 'Nzérékoré', NULL, NULL, 'AIRPORT', 'NATIONAL', FALSE, 'Wikipedia - List of airports in Guinea', 'https://en.wikipedia.org/wiki/List_of_airports_in_Guinea'),
('Guinea', 'GU', 'GUSA', NULL, 'Sangarédi Airport', 'Sangarédi', NULL, NULL, 'AIRPORT', 'NATIONAL', FALSE, 'Wikipedia - List of airports in Guinea', 'https://en.wikipedia.org/wiki/List_of_airports_in_Guinea'),
('Guinea', 'GU', 'GUSI', 'GII', 'Siguiri Airport', 'Siguiri', NULL, NULL, 'AIRPORT', 'NATIONAL', FALSE, 'Wikipedia - List of airports in Guinea', 'https://en.wikipedia.org/wiki/List_of_airports_in_Guinea'),
('Guinea-Bissau', 'GG', 'GGBF', NULL, 'Bafatá Airport', 'Bafatá', '12°10′35″N 14°39′30″W', NULL, 'AIRPORT', 'NATIONAL', FALSE, 'Wikipedia - List of airports in Guinea-Bissau', 'https://en.wikipedia.org/wiki/List_of_airports_in_Guinea-Bissau'),
('Guinea-Bissau', 'GG', 'GGOV', 'OXB', 'Osvaldo Vieiro International Airport', 'Bissau', '11°53′41″N 15°39′13″W', NULL, 'AIRPORT', 'INTERNATIONAL', FALSE, 'Wikipedia - List of airports in Guinea-Bissau', 'https://en.wikipedia.org/wiki/List_of_airports_in_Guinea-Bissau'),
('Guinea-Bissau', 'GG', 'GGBU', 'BQE', 'Bubaque Airport', 'Bubaque', '11°17′N 15°50′W', NULL, 'AIRPORT', 'NATIONAL', FALSE, 'Wikipedia - List of airports in Guinea-Bissau', 'https://en.wikipedia.org/wiki/List_of_airports_in_Guinea-Bissau'),
('Guinea-Bissau', 'GG', 'GGCF', NULL, 'Cufar Airport', 'Cufar', '11°17′17″N 15°10′50″W', NULL, 'AIRPORT', 'NATIONAL', FALSE, 'Wikipedia - List of airports in Guinea-Bissau', 'https://en.wikipedia.org/wiki/List_of_airports_in_Guinea-Bissau'),
('Guinea-Bissau', 'GG', 'GGGB', NULL, 'Nova Lamego Airport', 'Gabú', '12°17′30″N 14°14′10″W', NULL, 'AIRPORT', 'NATIONAL', FALSE, 'Wikipedia - List of airports in Guinea-Bissau', 'https://en.wikipedia.org/wiki/List_of_airports_in_Guinea-Bissau'),
('Liberia', 'GL', 'GLBU', 'UCN', 'Buchanan Airport', 'Buchanan', NULL, NULL, 'AIRPORT', 'NATIONAL', FALSE, 'Wikipedia - List of airports in Liberia', 'https://en.wikipedia.org/wiki/List_of_airports_in_Liberia'),
('Liberia', 'GL', 'GLLB', NULL, 'Lamco Airport', 'Buchanan', NULL, NULL, 'AIRPORT', 'NATIONAL', FALSE, 'Wikipedia - List of airports in Liberia', 'https://en.wikipedia.org/wiki/List_of_airports_in_Liberia'),
('Liberia', 'GL', 'GLCP', 'CPA', 'Cape Palmas Airport', 'Harper (Cape Palmas)', NULL, NULL, 'AIRPORT', 'NATIONAL', FALSE, 'Wikipedia - List of airports in Liberia', 'https://en.wikipedia.org/wiki/List_of_airports_in_Liberia'),
('Liberia', 'GL', 'GLGE', 'SNI', 'Greenville/Sinoe Airport', 'Greenville', NULL, NULL, 'AIRPORT', 'NATIONAL', FALSE, 'Wikipedia - List of airports in Liberia', 'https://en.wikipedia.org/wiki/List_of_airports_in_Liberia'),
('Liberia', 'GL', 'GLRB', 'ROB', 'Roberts International Airport', 'Harbel', NULL, NULL, 'AIRPORT', 'INTERNATIONAL', FALSE, 'Wikipedia - List of airports in Liberia', 'https://en.wikipedia.org/wiki/List_of_airports_in_Liberia'),
('Liberia', 'GL', 'GLMR', 'MLW', 'Spriggs Payne Airport', 'Monrovia', NULL, NULL, 'AIRPORT', 'NATIONAL', FALSE, 'Wikipedia - List of airports in Liberia', 'https://en.wikipedia.org/wiki/List_of_airports_in_Liberia'),
('Liberia', 'GL', 'GLNA', 'NIA', 'Nimba Airport', 'Nimba', NULL, NULL, 'AIRPORT', 'NATIONAL', FALSE, 'Wikipedia - List of airports in Liberia', 'https://en.wikipedia.org/wiki/List_of_airports_in_Liberia'),
('Liberia', 'GL', 'GLST', 'SAZ', 'Sasstown Airport', 'Sasstown', NULL, NULL, 'AIRPORT', 'NATIONAL', FALSE, 'Wikipedia - List of airports in Liberia', 'https://en.wikipedia.org/wiki/List_of_airports_in_Liberia'),
('Liberia', 'GL', 'GLTN', 'THC', 'Tchien Airport', 'Tchien', NULL, NULL, 'AIRPORT', 'NATIONAL', FALSE, 'Wikipedia - List of airports in Liberia', 'https://en.wikipedia.org/wiki/List_of_airports_in_Liberia'),
('Liberia', 'GL', 'GLVA', 'VOI', 'Voinjama Airport', 'Voinjama', NULL, NULL, 'AIRPORT', 'NATIONAL', FALSE, 'Wikipedia - List of airports in Liberia', 'https://en.wikipedia.org/wiki/List_of_airports_in_Liberia'),
('Mali', 'GA', 'GAAO', NULL, 'Ansongo Airport', 'Ansongo', NULL, NULL, 'AIRPORT', 'NATIONAL', FALSE, 'Wikipedia - List of airports in Mali', 'https://en.wikipedia.org/wiki/List_of_airports_in_Mali'),
('Mali', 'GA', 'GABF', NULL, 'Bafoulabe Airport', 'Bafoulabe', NULL, NULL, 'AIRPORT', 'NATIONAL', FALSE, 'Wikipedia - List of airports in Mali', 'https://en.wikipedia.org/wiki/List_of_airports_in_Mali'),
('Mali', 'GA', 'GABS', 'BKO', 'Modibo Keita International Airport', 'Bamako', NULL, NULL, 'AIRPORT', 'INTERNATIONAL', FALSE, 'Wikipedia - List of airports in Mali', 'https://en.wikipedia.org/wiki/List_of_airports_in_Mali'),
('Mali', 'GA', 'GABD', NULL, 'Bandiagara Airport', 'Bandiagara', NULL, NULL, 'AIRPORT', 'NATIONAL', FALSE, 'Wikipedia - List of airports in Mali', 'https://en.wikipedia.org/wiki/List_of_airports_in_Mali'),
('Mali', 'GA', 'GABG', NULL, 'Bougouni Airport', 'Bougouni', NULL, NULL, 'AIRPORT', 'NATIONAL', FALSE, 'Wikipedia - List of airports in Mali', 'https://en.wikipedia.org/wiki/List_of_airports_in_Mali'),
('Mali', 'GA', 'GABR', NULL, 'Bourem Airport', 'Bourem', NULL, NULL, 'AIRPORT', 'NATIONAL', FALSE, 'Wikipedia - List of airports in Mali', 'https://en.wikipedia.org/wiki/List_of_airports_in_Mali'),
('Mali', 'GA', 'GADZ', NULL, 'Douentza Airport', 'Douentza', NULL, NULL, 'AIRPORT', 'NATIONAL', FALSE, 'Wikipedia - List of airports in Mali', 'https://en.wikipedia.org/wiki/List_of_airports_in_Mali'),
('Mali', 'GA', 'GAGM', 'GUD', 'Goundam Airport', 'Goundam', NULL, NULL, 'AIRPORT', 'NATIONAL', FALSE, 'Wikipedia - List of airports in Mali', 'https://en.wikipedia.org/wiki/List_of_airports_in_Mali'),
('Mali', 'GA', 'GAGO', 'GAQ', 'Gao International Airport', 'Gao', NULL, NULL, 'AIRPORT', 'INTERNATIONAL', FALSE, 'Wikipedia - List of airports in Mali', 'https://en.wikipedia.org/wiki/List_of_airports_in_Mali'),
('Mali', 'GA', 'GAKY', 'KYS', 'Kayes Dag-Dag Airport', 'Kayes', NULL, NULL, 'AIRPORT', 'NATIONAL', FALSE, 'Wikipedia - List of airports in Mali', 'https://en.wikipedia.org/wiki/List_of_airports_in_Mali'),
('Mali', 'GA', 'GAKA', 'KNZ', 'Kenieba Airport', 'Kenieba', NULL, NULL, 'AIRPORT', 'NATIONAL', FALSE, 'Wikipedia - List of airports in Mali', 'https://en.wikipedia.org/wiki/List_of_airports_in_Mali'),
('Mali', 'GA', 'GAKL', NULL, 'Kidal Airport', 'Kidal', NULL, NULL, 'AIRPORT', 'NATIONAL', FALSE, 'Wikipedia - List of airports in Mali', 'https://en.wikipedia.org/wiki/List_of_airports_in_Mali'),
('Mali', 'GA', 'GAKT', NULL, 'Kita Airport', 'Kita', NULL, NULL, 'AIRPORT', 'NATIONAL', FALSE, 'Wikipedia - List of airports in Mali', 'https://en.wikipedia.org/wiki/List_of_airports_in_Mali'),
('Mali', 'GA', 'GAKN', NULL, 'Kolokani Airport', 'Kolokani', NULL, NULL, 'AIRPORT', 'NATIONAL', FALSE, 'Wikipedia - List of airports in Mali', 'https://en.wikipedia.org/wiki/List_of_airports_in_Mali'),
('Mali', 'GA', 'GAKO', 'KTX', 'Koutiala Airport', 'Koutiala', NULL, NULL, 'AIRPORT', 'NATIONAL', FALSE, 'Wikipedia - List of airports in Mali', 'https://en.wikipedia.org/wiki/List_of_airports_in_Mali'),
('Mali', 'GA', 'GAMA', NULL, 'Markala Airport', 'Markala', NULL, NULL, 'AIRPORT', 'NATIONAL', FALSE, 'Wikipedia - List of airports in Mali', 'https://en.wikipedia.org/wiki/List_of_airports_in_Mali'),
('Mali', 'GA', 'GAMK', NULL, 'Menaka Airport', 'Ménaka', NULL, NULL, 'AIRPORT', 'NATIONAL', FALSE, 'Wikipedia - List of airports in Mali', 'https://en.wikipedia.org/wiki/List_of_airports_in_Mali'),
('Mali', 'GA', 'GAMB', 'MZI', 'Mopti Airport', 'Mopti', NULL, NULL, 'AIRPORT', 'NATIONAL', FALSE, 'Wikipedia - List of airports in Mali', 'https://en.wikipedia.org/wiki/List_of_airports_in_Mali'),
('Mali', 'GA', 'GANK', 'NRM', 'Keibane Airport', 'Nara', NULL, NULL, 'AIRPORT', 'NATIONAL', FALSE, 'Wikipedia - List of airports in Mali', 'https://en.wikipedia.org/wiki/List_of_airports_in_Mali'),
('Mali', 'GA', 'GANF', NULL, 'Niafunké Airport', 'Niafunké', NULL, NULL, 'AIRPORT', 'NATIONAL', FALSE, 'Wikipedia - List of airports in Mali', 'https://en.wikipedia.org/wiki/List_of_airports_in_Mali'),
('Mali', 'GA', 'GANR', 'NIX', 'Nioro Airport', 'Nioro du Sahel', NULL, NULL, 'AIRPORT', 'NATIONAL', FALSE, 'Wikipedia - List of airports in Mali', 'https://en.wikipedia.org/wiki/List_of_airports_in_Mali'),
('Mali', 'GA', 'GASK', 'KSS', 'Sikasso Airport', 'Sikasso', NULL, NULL, 'AIRPORT', 'NATIONAL', FALSE, 'Wikipedia - List of airports in Mali', 'https://en.wikipedia.org/wiki/List_of_airports_in_Mali'),
('Mali', 'GA', 'GATS', NULL, 'Tessalit Airport', 'Tessalit', NULL, NULL, 'AIRPORT', 'NATIONAL', FALSE, 'Wikipedia - List of airports in Mali', 'https://en.wikipedia.org/wiki/List_of_airports_in_Mali'),
('Mali', 'GA', 'GATB', 'TOM', 'Timbuktu Airport', 'Timbuktu', NULL, NULL, 'AIRPORT', 'NATIONAL', FALSE, 'Wikipedia - List of airports in Mali', 'https://en.wikipedia.org/wiki/List_of_airports_in_Mali'),
('Mali', 'GA', 'GAYE', 'EYL', 'Yélimané Airport', 'Yélimané', NULL, NULL, 'AIRPORT', 'NATIONAL', FALSE, 'Wikipedia - List of airports in Mali', 'https://en.wikipedia.org/wiki/List_of_airports_in_Mali'),
('Mauritania', 'GQ', 'GQNA', 'AEO', 'Aioun el Atrouss Airport', 'Aioun el Atrouss', NULL, NULL, 'AIRPORT', 'NATIONAL', FALSE, 'Wikipedia - List of airports in Mauritania', 'https://en.wikipedia.org/wiki/List_of_airports_in_Mauritania'),
('Mauritania', 'GQ', 'GQNJ', 'AJJ', 'Akjoujt Airport', 'Akjoujt', NULL, NULL, 'AIRPORT', 'NATIONAL', FALSE, 'Wikipedia - List of airports in Mauritania', 'https://en.wikipedia.org/wiki/List_of_airports_in_Mauritania'),
('Mauritania', 'GQ', 'GQPA', 'ATR', 'Atar International Airport', 'Atar', NULL, NULL, 'AIRPORT', 'INTERNATIONAL', FALSE, 'Wikipedia - List of airports in Mauritania', 'https://en.wikipedia.org/wiki/List_of_airports_in_Mauritania'),
('Mauritania', 'GQ', 'GQPT', NULL, 'Bir Moghrein Airport', 'Bir Moghrein', NULL, NULL, 'AIRPORT', 'NATIONAL', FALSE, 'Wikipedia - List of airports in Mauritania', 'https://en.wikipedia.org/wiki/List_of_airports_in_Mauritania'),
('Mauritania', 'GQ', 'GQNE', 'BGH', 'Abbaye Airport', 'Boghé', NULL, NULL, 'AIRPORT', 'NATIONAL', FALSE, 'Wikipedia - List of airports in Mauritania', 'https://en.wikipedia.org/wiki/List_of_airports_in_Mauritania'),
('Mauritania', 'GQ', 'GQNB', 'OTL', 'Boutilimit Airport', 'Boutilimit', NULL, NULL, 'AIRPORT', 'NATIONAL', FALSE, 'Wikipedia - List of airports in Mauritania', 'https://en.wikipedia.org/wiki/List_of_airports_in_Mauritania'),
('Mauritania', 'GQ', 'GQPF', 'FGD', 'Fderik Airport', 'Fderik', NULL, NULL, 'AIRPORT', 'NATIONAL', FALSE, 'Wikipedia - List of airports in Mauritania', 'https://en.wikipedia.org/wiki/List_of_airports_in_Mauritania'),
('Mauritania', 'GQ', 'GQNK', 'KED', 'Kaédi Airport', 'Kaédi', NULL, NULL, 'AIRPORT', 'NATIONAL', FALSE, 'Wikipedia - List of airports in Mauritania', 'https://en.wikipedia.org/wiki/List_of_airports_in_Mauritania'),
('Mauritania', 'GQ', 'GQNF', 'KFA', 'Kiffa Airport', 'Kiffa', NULL, NULL, 'AIRPORT', 'NATIONAL', FALSE, 'Wikipedia - List of airports in Mauritania', 'https://en.wikipedia.org/wiki/List_of_airports_in_Mauritania'),
('Mauritania', 'GQ', 'GQNL', 'MOM', 'Letfotar Airport', 'Moudjeria', NULL, NULL, 'AIRPORT', 'NATIONAL', FALSE, 'Wikipedia - List of airports in Mauritania', 'https://en.wikipedia.org/wiki/List_of_airports_in_Mauritania'),
('Mauritania', 'GQ', 'GQNI', 'EMN', 'Néma Airport', 'Néma', NULL, NULL, 'AIRPORT', 'NATIONAL', FALSE, 'Wikipedia - List of airports in Mauritania', 'https://en.wikipedia.org/wiki/List_of_airports_in_Mauritania'),
('Mauritania', 'GQ', 'GQPP', 'NDB', 'Nouadhibou International Airport', 'Nouadhibou', NULL, NULL, 'AIRPORT', 'INTERNATIONAL', FALSE, 'Wikipedia - List of airports in Mauritania', 'https://en.wikipedia.org/wiki/List_of_airports_in_Mauritania'),
('Mauritania', 'GQ', 'GQNN', NULL, 'Nouakchott International Airport', 'Nouakchott', NULL, NULL, 'AIRPORT', 'INTERNATIONAL', FALSE, 'Wikipedia - List of airports in Mauritania', 'https://en.wikipedia.org/wiki/List_of_airports_in_Mauritania'),
('Mauritania', 'GQ', 'GQNO', 'NKC', 'Nouakchott–Oumtounsy International Airport', 'Nouakchott', NULL, NULL, 'AIRPORT', 'INTERNATIONAL', FALSE, 'Wikipedia - List of airports in Mauritania', 'https://en.wikipedia.org/wiki/List_of_airports_in_Mauritania'),
('Mauritania', 'GQ', 'GQNS', 'SEY', 'Sélibaby Airport', 'Sélibaby', NULL, NULL, 'AIRPORT', 'NATIONAL', FALSE, 'Wikipedia - List of airports in Mauritania', 'https://en.wikipedia.org/wiki/List_of_airports_in_Mauritania'),
('Mauritania', 'GQ', 'GQNT', 'THT', 'Tamchakett Airport', 'Tamchekett', NULL, NULL, 'AIRPORT', 'NATIONAL', FALSE, 'Wikipedia - List of airports in Mauritania', 'https://en.wikipedia.org/wiki/List_of_airports_in_Mauritania'),
('Mauritania', 'GQ', 'GQNC', 'THI', 'Tichitt Airport', 'Tichitt', NULL, NULL, 'AIRPORT', 'NATIONAL', FALSE, 'Wikipedia - List of airports in Mauritania', 'https://en.wikipedia.org/wiki/List_of_airports_in_Mauritania'),
('Mauritania', 'GQ', 'GQND', 'TIY', 'Tidjikja Airport', 'Tidjikja', NULL, NULL, 'AIRPORT', 'NATIONAL', FALSE, 'Wikipedia - List of airports in Mauritania', 'https://en.wikipedia.org/wiki/List_of_airports_in_Mauritania'),
('Mauritania', 'GQ', 'GQNM', NULL, 'Dahara Airport', 'Timbedra', NULL, NULL, 'AIRPORT', 'NATIONAL', FALSE, 'Wikipedia - List of airports in Mauritania', 'https://en.wikipedia.org/wiki/List_of_airports_in_Mauritania'),
('Mauritania', 'GQ', 'GQNH', 'TMD', 'Timbedra Airport', 'Timbedra', NULL, NULL, 'AIRPORT', 'NATIONAL', FALSE, 'Wikipedia - List of airports in Mauritania', 'https://en.wikipedia.org/wiki/List_of_airports_in_Mauritania'),
('Mauritania', 'GQ', 'GQPZ', 'OUZ', 'Tazadit Airport', 'Zouérat', NULL, NULL, 'AIRPORT', 'NATIONAL', FALSE, 'Wikipedia - List of airports in Mauritania', 'https://en.wikipedia.org/wiki/List_of_airports_in_Mauritania'),
('Niger', 'DR', 'DRZA', 'AJY', 'Mano Dayak International Airport', 'Agadez', NULL, NULL, 'AIRPORT', 'INTERNATIONAL', FALSE, 'Wikipedia - List of airports in Niger', 'https://en.wikipedia.org/wiki/List_of_airports_in_Niger'),
('Niger', 'DR', 'DRZL', 'RLT', 'Arlit Airport', 'Arlit', NULL, NULL, 'AIRPORT', 'NATIONAL', FALSE, 'Wikipedia - List of airports in Niger', 'https://en.wikipedia.org/wiki/List_of_airports_in_Niger'),
('Niger', 'DR', 'DRZF', NULL, 'Diffa Airport', 'Diffa', NULL, NULL, 'AIRPORT', 'NATIONAL', FALSE, 'Wikipedia - List of airports in Niger', 'https://en.wikipedia.org/wiki/List_of_airports_in_Niger'),
('Niger', 'DR', 'DRZD', NULL, 'Dirkou Airport', 'Dirkou', NULL, NULL, 'AIRPORT', 'NATIONAL', FALSE, 'Wikipedia - List of airports in Niger', 'https://en.wikipedia.org/wiki/List_of_airports_in_Niger'),
('Niger', 'DR', 'DRRC', NULL, 'Dogondoutchi Airport', 'Dogondoutchi', NULL, NULL, 'AIRPORT', 'NATIONAL', FALSE, 'Wikipedia - List of airports in Niger', 'https://en.wikipedia.org/wiki/List_of_airports_in_Niger'),
('Niger', 'DR', 'DRRD', NULL, 'Dosso Airport', 'Dosso', NULL, NULL, 'AIRPORT', 'NATIONAL', FALSE, 'Wikipedia - List of airports in Niger', 'https://en.wikipedia.org/wiki/List_of_airports_in_Niger'),
('Niger', 'DR', 'DRRG', NULL, 'Gaya Airport', 'Gaya', NULL, NULL, 'AIRPORT', 'NATIONAL', FALSE, 'Wikipedia - List of airports in Niger', 'https://en.wikipedia.org/wiki/List_of_airports_in_Niger'),
('Niger', 'DR', 'DRZG', NULL, 'Goure Airport', 'Goure', NULL, NULL, 'AIRPORT', 'NATIONAL', FALSE, 'Wikipedia - List of airports in Niger', 'https://en.wikipedia.org/wiki/List_of_airports_in_Niger'),
('Niger', 'DR', 'DRZI', NULL, 'Iferouane Airport', 'Iferouane', NULL, NULL, 'AIRPORT', 'NATIONAL', FALSE, 'Wikipedia - List of airports in Niger', 'https://en.wikipedia.org/wiki/List_of_airports_in_Niger'),
('Niger', 'DR', 'DRRP', NULL, 'La Tapoa Airport', 'La Tapoa', NULL, NULL, 'AIRPORT', 'NATIONAL', FALSE, 'Wikipedia - List of airports in Niger', 'https://en.wikipedia.org/wiki/List_of_airports_in_Niger'),
('Niger', 'DR', 'DRZM', NULL, 'Maine-Soroa Airport', 'Maine-Soroa', NULL, NULL, 'AIRPORT', 'NATIONAL', FALSE, 'Wikipedia - List of airports in Niger', 'https://en.wikipedia.org/wiki/List_of_airports_in_Niger'),
('Niger', 'DR', 'DRRM', 'MFQ', 'Maradi Airport', 'Maradi', NULL, NULL, 'AIRPORT', 'NATIONAL', FALSE, 'Wikipedia - List of airports in Niger', 'https://en.wikipedia.org/wiki/List_of_airports_in_Niger'),
('Niger', 'DR', 'DRRN', 'NIM', 'Diori Hamani International Airport', 'Niamey', NULL, NULL, 'AIRPORT', 'INTERNATIONAL', FALSE, 'Wikipedia - List of airports in Niger', 'https://en.wikipedia.org/wiki/List_of_airports_in_Niger'),
('Niger', 'DR', 'DRRU', NULL, 'Ouallam Airport', 'Ouallam', NULL, NULL, 'AIRPORT', 'NATIONAL', FALSE, 'Wikipedia - List of airports in Niger', 'https://en.wikipedia.org/wiki/List_of_airports_in_Niger'),
('Niger', 'DR', 'DRRT', 'THZ', 'Tahoua Airport', 'Tahoua', NULL, NULL, 'AIRPORT', 'NATIONAL', FALSE, 'Wikipedia - List of airports in Niger', 'https://en.wikipedia.org/wiki/List_of_airports_in_Niger'),
('Niger', 'DR', 'DRRE', NULL, 'Téra Airport', 'Téra', NULL, NULL, 'AIRPORT', 'NATIONAL', FALSE, 'Wikipedia - List of airports in Niger', 'https://en.wikipedia.org/wiki/List_of_airports_in_Niger'),
('Niger', 'DR', 'DRRA', NULL, 'Tessaoua Airport', 'Tessaoua', NULL, NULL, 'AIRPORT', 'NATIONAL', FALSE, 'Wikipedia - List of airports in Niger', 'https://en.wikipedia.org/wiki/List_of_airports_in_Niger'),
('Niger', 'DR', 'DRRL', NULL, 'Tillabéri Airport', 'Tillabéri', NULL, NULL, 'AIRPORT', 'NATIONAL', FALSE, 'Wikipedia - List of airports in Niger', 'https://en.wikipedia.org/wiki/List_of_airports_in_Niger'),
('Niger', 'DR', 'DRRZ', NULL, 'Tillia Airport', 'Tillia', NULL, NULL, 'AIRPORT', 'NATIONAL', FALSE, 'Wikipedia - List of airports in Niger', 'https://en.wikipedia.org/wiki/List_of_airports_in_Niger'),
('Niger', 'DR', 'DRZR', 'ZND', 'Zinder International Airport', 'Zinder', NULL, NULL, 'AIRPORT', 'INTERNATIONAL', FALSE, 'Wikipedia - List of airports in Niger', 'https://en.wikipedia.org/wiki/List_of_airports_in_Niger')
ON DUPLICATE KEY UPDATE
  country_name = VALUES(country_name),
  icao_prefix = VALUES(icao_prefix),
  iata_code = VALUES(iata_code),
  name = VALUES(name),
  city = VALUES(city),
  raw_coordinates = VALUES(raw_coordinates),
  elevation_ft = VALUES(elevation_ft),
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
FROM tmp_west_africa_2_airports t
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
  NULL,
  CASE
    WHEN t.raw_coordinates = '12°10′35″N 14°39′30″W' THEN 12.1763889
    WHEN t.raw_coordinates = '11°53′41″N 15°39′13″W' THEN 11.8947222
    WHEN t.raw_coordinates = '11°17′N 15°50′W' THEN 11.2833333
    WHEN t.raw_coordinates = '11°17′17″N 15°10′50″W' THEN 11.2880556
    WHEN t.raw_coordinates = '12°17′30″N 14°14′10″W' THEN 12.2916667
    ELSE NULL
  END AS latitude,
  CASE
    WHEN t.raw_coordinates = '12°10′35″N 14°39′30″W' THEN -14.6583333
    WHEN t.raw_coordinates = '11°53′41″N 15°39′13″W' THEN -15.6536111
    WHEN t.raw_coordinates = '11°17′N 15°50′W' THEN -15.8333333
    WHEN t.raw_coordinates = '11°17′17″N 15°10′50″W' THEN -15.1805556
    WHEN t.raw_coordinates = '12°17′30″N 14°14′10″W' THEN -14.2361111
    ELSE NULL
  END AS longitude,
  t.elevation_ft,
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
FROM tmp_west_africa_2_airports t
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

-- Diagnostics: these rows would not import if a country name is missing in countries.
SELECT
  t.country_name,
  COUNT(*) AS rows_not_imported_missing_country
FROM tmp_west_africa_2_airports t
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
  SUM(CASE WHEN a.elevation_ft IS NOT NULL THEN 1 ELSE 0 END) AS airports_with_elevation
FROM airports a
JOIN countries c
  ON c.id = a.country_id
WHERE c.name IN ('Guinea', 'Guinea-Bissau', 'Liberia', 'Mali', 'Mauritania', 'Niger')
  AND c.world_region_code = 'AFRICA'
GROUP BY c.name
ORDER BY c.name;
