-- Starter airport seed.
-- This is a small curated starter set for development only.
-- It will be replaced or expanded by a more complete worldwide import.

USE icaro_ops;

INSERT INTO airports (
  icao_prefix_id,
  icao_code,
  iata_code,
  name,
  city,
  country_name,
  subdivision_name,
  latitude,
  longitude,
  elevation_ft,
  is_civilian,
  is_commercial,
  is_military,
  is_closed,
  data_source_name,
  data_source_url,
  data_quality
) VALUES
((SELECT id FROM icao_prefixes WHERE prefix = 'LI'), 'LIRA', 'CIA', 'Rome Ciampino Airport', 'Rome', 'Italy', NULL, 41.7994, 12.5949, 427, TRUE, TRUE, FALSE, FALSE, 'Manual seed', NULL, 'PARTIAL'),
((SELECT id FROM icao_prefixes WHERE prefix = 'LI'), 'LIMJ', 'GOA', 'Genoa Cristoforo Colombo Airport', 'Genoa', 'Italy', NULL, 44.4133, 8.8375, 13, TRUE, TRUE, FALSE, FALSE, 'Manual seed', NULL, 'PARTIAL'),
((SELECT id FROM icao_prefixes WHERE prefix = 'LI'), 'LICC', 'CTA', 'Catania Fontanarossa Airport', 'Catania', 'Italy', NULL, 37.4668, 15.0664, 39, TRUE, TRUE, FALSE, FALSE, 'Manual seed', NULL, 'PARTIAL'),
((SELECT id FROM icao_prefixes WHERE prefix = 'EG'), 'EGTE', 'EXT', 'Exeter Airport', 'Exeter', 'United Kingdom', NULL, 50.7344, -3.4139, 102, TRUE, TRUE, FALSE, FALSE, 'Manual seed', NULL, 'PARTIAL'),
((SELECT id FROM icao_prefixes WHERE prefix = 'LF'), 'LFMD', 'CEQ', 'Cannes Mandelieu Airport', 'Cannes', 'France', NULL, 43.542, 6.9535, 13, TRUE, TRUE, FALSE, FALSE, 'Manual seed', NULL, 'PARTIAL'),
((SELECT id FROM icao_prefixes WHERE prefix = 'ED'), 'EDFH', 'HHN', 'Frankfurt Hahn Airport', 'Hahn', 'Germany', NULL, 49.9487, 7.2639, 1649, TRUE, TRUE, FALSE, FALSE, 'Manual seed', NULL, 'PARTIAL'),
((SELECT id FROM icao_prefixes WHERE prefix = 'LE'), 'LEST', 'SCQ', 'Santiago de Compostela Airport', 'Santiago de Compostela', 'Spain', NULL, 42.8963, -8.4151, 1213, TRUE, TRUE, FALSE, FALSE, 'Manual seed', NULL, 'PARTIAL'),
((SELECT id FROM icao_prefixes WHERE prefix = 'K'), 'KBLI', 'BLI', 'Bellingham International Airport', 'Bellingham', 'United States', 'Washington', 48.7928, -122.5375, 170, TRUE, TRUE, FALSE, FALSE, 'Manual seed', NULL, 'PARTIAL'),
((SELECT id FROM icao_prefixes WHERE prefix = 'K'), 'KAVL', 'AVL', 'Asheville Regional Airport', 'Asheville', 'United States', 'North Carolina', 35.4362, -82.5418, 2165, TRUE, TRUE, FALSE, FALSE, 'Manual seed', NULL, 'PARTIAL'),
((SELECT id FROM icao_prefixes WHERE prefix = 'C'), 'CYKF', 'YKF', 'Region of Waterloo International Airport', 'Waterloo', 'Canada', 'Ontario', 43.4608, -80.3786, 1055, TRUE, TRUE, FALSE, FALSE, 'Manual seed', NULL, 'PARTIAL'),
((SELECT id FROM icao_prefixes WHERE prefix = 'SB'), 'SBCT', 'CWB', 'Afonso Pena International Airport', 'Curitiba', 'Brazil', 'Parana', -25.5285, -49.1758, 2988, TRUE, TRUE, FALSE, FALSE, 'Manual seed', NULL, 'PARTIAL'),
((SELECT id FROM icao_prefixes WHERE prefix = 'SA'), 'SAME', 'MDZ', 'Governor Francisco Gabrielli International Airport', 'Mendoza', 'Argentina', 'Mendoza', -32.8317, -68.7929, 2310, TRUE, TRUE, FALSE, FALSE, 'Manual seed', NULL, 'PARTIAL'),
((SELECT id FROM icao_prefixes WHERE prefix = 'FA'), 'FACT', 'CPT', 'Cape Town International Airport', 'Cape Town', 'South Africa', 'Western Cape', -33.9648, 18.6017, 151, TRUE, TRUE, FALSE, FALSE, 'Manual seed', NULL, 'PARTIAL'),
((SELECT id FROM icao_prefixes WHERE prefix = 'HK'), 'HKMO', 'MBA', 'Moi International Airport', 'Mombasa', 'Kenya', NULL, -4.0348, 39.5942, 200, TRUE, TRUE, FALSE, FALSE, 'Manual seed', NULL, 'PARTIAL'),
((SELECT id FROM icao_prefixes WHERE prefix = 'YB'), 'YBCS', 'CNS', 'Cairns Airport', 'Cairns', 'Australia', 'Queensland', -16.8858, 145.7553, 10, TRUE, TRUE, FALSE, FALSE, 'Manual seed', NULL, 'PARTIAL'),
((SELECT id FROM icao_prefixes WHERE prefix = 'RJ'), 'RJBB', 'KIX', 'Kansai International Airport', 'Osaka', 'Japan', NULL, 34.4273, 135.244, 26, TRUE, TRUE, FALSE, FALSE, 'Manual seed', NULL, 'PARTIAL'),
((SELECT id FROM icao_prefixes WHERE prefix = 'VO'), 'VOCI', 'COK', 'Cochin International Airport', 'Kochi', 'India', 'Kerala', 10.152, 76.4019, 30, TRUE, TRUE, FALSE, FALSE, 'Manual seed', NULL, 'PARTIAL'),
((SELECT id FROM icao_prefixes WHERE prefix = 'AG'), 'AGGH', 'HIR', 'Honiara International Airport', 'Honiara', 'Solomon Islands', NULL, -9.428, 160.0548, 28, TRUE, TRUE, FALSE, FALSE, 'Manual seed', NULL, 'PARTIAL')
ON DUPLICATE KEY UPDATE
  icao_prefix_id = VALUES(icao_prefix_id),
  iata_code = VALUES(iata_code),
  name = VALUES(name),
  city = VALUES(city),
  country_name = VALUES(country_name),
  subdivision_name = VALUES(subdivision_name),
  latitude = VALUES(latitude),
  longitude = VALUES(longitude),
  elevation_ft = VALUES(elevation_ft),
  is_civilian = VALUES(is_civilian),
  is_commercial = VALUES(is_commercial),
  is_military = VALUES(is_military),
  is_closed = VALUES(is_closed),
  data_source_name = VALUES(data_source_name),
  data_source_url = VALUES(data_source_url),
  data_quality = VALUES(data_quality);
