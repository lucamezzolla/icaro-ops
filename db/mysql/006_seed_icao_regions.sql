-- ICAO region seed.
-- Broad first-letter groups.

USE icaro_ops;

INSERT INTO icao_regions (region_code, name, description, sort_order) VALUES
('A', 'Western South Pacific', 'ICAO region group A.', 10),
('B', 'Northern Atlantic', 'ICAO region group B.', 20),
('C', 'Canada', 'ICAO region group C.', 30),
('D', 'Western Africa', 'ICAO region group D.', 40),
('E', 'Northern Europe', 'ICAO region group E.', 50),
('F', 'Southern Africa and Indian Ocean', 'ICAO region group F.', 60),
('G', 'Western and Northern Africa', 'ICAO region group G.', 70),
('H', 'Eastern Africa', 'ICAO region group H.', 80),
('K', 'Contiguous United States', 'ICAO region group K.', 90),
('L', 'Southern Europe and Mediterranean', 'ICAO region group L.', 100),
('M', 'Central America, Mexico and Caribbean', 'ICAO region group M.', 110),
('N', 'South Pacific', 'ICAO region group N.', 120),
('O', 'Middle East and Central Asia', 'ICAO region group O.', 130),
('P', 'Northern Pacific', 'ICAO region group P.', 140),
('R', 'East Asia', 'ICAO region group R.', 150),
('S', 'South America', 'ICAO region group S.', 160),
('T', 'Caribbean', 'ICAO region group T.', 170),
('U', 'Russia and former Soviet states', 'ICAO region group U.', 180),
('V', 'South Asia and mainland Southeast Asia', 'ICAO region group V.', 190),
('W', 'Maritime Southeast Asia', 'ICAO region group W.', 200),
('Y', 'Australia', 'ICAO region group Y.', 210),
('Z', 'China, Mongolia and North Korea', 'ICAO region group Z.', 220)
ON DUPLICATE KEY UPDATE
  name = VALUES(name),
  description = VALUES(description),
  sort_order = VALUES(sort_order),
  is_active = TRUE;
