-- Starter airport seed.
-- This is intentionally small and will be replaced/expanded later with a curated worldwide airport dataset.

INSERT INTO airports (
  icao_code,
  iata_code,
  name,
  city,
  country,
  continent,
  latitude,
  longitude,
  airport_size,
  is_starter_base
) VALUES
('LIRA', 'CIA', 'Rome Ciampino Airport', 'Rome', 'Italy', 'Europe', 41.7994, 12.5949, 'SMALL_COMMERCIAL', 1),
('LIMJ', 'GOA', 'Genoa Cristoforo Colombo Airport', 'Genoa', 'Italy', 'Europe', 44.4133, 8.8375, 'SMALL_COMMERCIAL', 1),
('LICC', 'CTA', 'Catania Fontanarossa Airport', 'Catania', 'Italy', 'Europe', 37.4668, 15.0664, 'SMALL_COMMERCIAL', 1),
('EGTE', 'EXT', 'Exeter Airport', 'Exeter', 'United Kingdom', 'Europe', 50.7344, -3.4139, 'SMALL_COMMERCIAL', 1),
('LFMD', 'CEQ', 'Cannes Mandelieu Airport', 'Cannes', 'France', 'Europe', 43.542, 6.9535, 'SMALL_COMMERCIAL', 1),
('EDFH', 'HHN', 'Frankfurt Hahn Airport', 'Hahn', 'Germany', 'Europe', 49.9487, 7.2639, 'SMALL_COMMERCIAL', 1),
('LEST', 'SCQ', 'Santiago de Compostela Airport', 'Santiago de Compostela', 'Spain', 'Europe', 42.8963, -8.4151, 'SMALL_COMMERCIAL', 1),
('KBLI', 'BLI', 'Bellingham International Airport', 'Bellingham', 'United States', 'North America', 48.7928, -122.5375, 'SMALL_COMMERCIAL', 1),
('KAVL', 'AVL', 'Asheville Regional Airport', 'Asheville', 'United States', 'North America', 35.4362, -82.5418, 'SMALL_COMMERCIAL', 1),
('CYKF', 'YKF', 'Region of Waterloo International Airport', 'Waterloo', 'Canada', 'North America', 43.4608, -80.3786, 'SMALL_COMMERCIAL', 1),
('SBCT', 'CWB', 'Afonso Pena International Airport', 'Curitiba', 'Brazil', 'South America', -25.5285, -49.1758, 'SMALL_COMMERCIAL', 1),
('SAME', 'MDZ', 'Governor Francisco Gabrielli International Airport', 'Mendoza', 'Argentina', 'South America', -32.8317, -68.7929, 'SMALL_COMMERCIAL', 1),
('FACT', 'CPT', 'Cape Town International Airport', 'Cape Town', 'South Africa', 'Africa', -33.9648, 18.6017, 'SMALL_COMMERCIAL', 1),
('HKMO', 'MBA', 'Moi International Airport', 'Mombasa', 'Kenya', 'Africa', -4.0348, 39.5942, 'SMALL_COMMERCIAL', 1),
('YBCS', 'CNS', 'Cairns Airport', 'Cairns', 'Australia', 'Oceania', -16.8858, 145.7553, 'SMALL_COMMERCIAL', 1),
('NZQN', 'ZQN', 'Queenstown Airport', 'Queenstown', 'New Zealand', 'Oceania', -45.0211, 168.7392, 'SMALL_COMMERCIAL', 1),
('RJBB', 'KIX', 'Kansai International Airport', 'Osaka', 'Japan', 'Asia', 34.4273, 135.244, 'SMALL_COMMERCIAL', 1),
('VOCI', 'COK', 'Cochin International Airport', 'Kochi', 'India', 'Asia', 10.152, 76.4019, 'SMALL_COMMERCIAL', 1);
