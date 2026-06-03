-- World region seed.
-- Source list supplied by project design notes.

USE icaro_ops;

INSERT INTO world_regions (code, name, sort_order) VALUES
('AFRICA', 'Africa', 10),
('ANTARCTICA', 'Antarctica', 20),
('ASIA', 'Asia', 30),
('EUROPE', 'Europe', 40),
('NORTH_AMERICA', 'North America', 50),
('OCEANIA', 'Oceania', 60),
('SOUTH_AMERICA', 'South America', 70)
ON DUPLICATE KEY UPDATE
  name = VALUES(name),
  sort_order = VALUES(sort_order),
  is_active = TRUE;
