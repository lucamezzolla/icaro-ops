-- ICAO prefix seed.
-- This seed is intentionally incomplete and will be expanded gradually.
-- Prefixes and country/area names are stored in English.

USE icaro_ops;

INSERT INTO icao_prefixes (
  icao_region_id,
  prefix,
  country_name,
  area_name
) VALUES
((SELECT id FROM icao_regions WHERE region_code = 'A'), 'AG', 'Solomon Islands', NULL),
((SELECT id FROM icao_regions WHERE region_code = 'C'), 'C', 'Canada', NULL),
((SELECT id FROM icao_regions WHERE region_code = 'D'), 'DN', 'Nigeria', NULL),
((SELECT id FROM icao_regions WHERE region_code = 'E'), 'EG', 'United Kingdom', NULL),
((SELECT id FROM icao_regions WHERE region_code = 'E'), 'EI', 'Ireland', NULL),
((SELECT id FROM icao_regions WHERE region_code = 'E'), 'EK', 'Denmark', NULL),
((SELECT id FROM icao_regions WHERE region_code = 'E'), 'EN', 'Norway', NULL),
((SELECT id FROM icao_regions WHERE region_code = 'E'), 'ES', 'Sweden', NULL),
((SELECT id FROM icao_regions WHERE region_code = 'E'), 'EF', 'Finland', NULL),
((SELECT id FROM icao_regions WHERE region_code = 'F'), 'FA', 'South Africa', NULL),
((SELECT id FROM icao_regions WHERE region_code = 'G'), 'GC', 'Spain', 'Canary Islands'),
((SELECT id FROM icao_regions WHERE region_code = 'H'), 'HK', 'Kenya', NULL),
((SELECT id FROM icao_regions WHERE region_code = 'K'), 'K', 'United States', 'Contiguous United States'),
((SELECT id FROM icao_regions WHERE region_code = 'L'), 'LI', 'Italy', NULL),
((SELECT id FROM icao_regions WHERE region_code = 'L'), 'LF', 'France', NULL),
((SELECT id FROM icao_regions WHERE region_code = 'L'), 'LE', 'Spain', 'Mainland Spain and Balearic Islands'),
((SELECT id FROM icao_regions WHERE region_code = 'L'), 'LP', 'Portugal', NULL),
((SELECT id FROM icao_regions WHERE region_code = 'L'), 'LG', 'Greece', NULL),
((SELECT id FROM icao_regions WHERE region_code = 'L'), 'LS', 'Switzerland', NULL),
((SELECT id FROM icao_regions WHERE region_code = 'L'), 'ED', 'Germany', 'Civil airports'),
((SELECT id FROM icao_regions WHERE region_code = 'M'), 'MM', 'Mexico', NULL),
((SELECT id FROM icao_regions WHERE region_code = 'N'), 'NS', 'Samoa', NULL),
((SELECT id FROM icao_regions WHERE region_code = 'O'), 'OM', 'United Arab Emirates', NULL),
((SELECT id FROM icao_regions WHERE region_code = 'P'), 'PH', 'United States', 'Hawaii'),
((SELECT id FROM icao_regions WHERE region_code = 'R'), 'RJ', 'Japan', 'Honshu, Kyushu and nearby islands'),
((SELECT id FROM icao_regions WHERE region_code = 'S'), 'SB', 'Brazil', NULL),
((SELECT id FROM icao_regions WHERE region_code = 'S'), 'SA', 'Argentina', NULL),
((SELECT id FROM icao_regions WHERE region_code = 'S'), 'SC', 'Chile', NULL),
((SELECT id FROM icao_regions WHERE region_code = 'T'), 'TN', 'Netherlands Caribbean', NULL),
((SELECT id FROM icao_regions WHERE region_code = 'U'), 'UU', 'Russia', 'Moscow area'),
((SELECT id FROM icao_regions WHERE region_code = 'V'), 'VO', 'India', 'Southern India'),
((SELECT id FROM icao_regions WHERE region_code = 'V'), 'VT', 'Thailand', NULL),
((SELECT id FROM icao_regions WHERE region_code = 'W'), 'WI', 'Indonesia', 'Java and nearby areas'),
((SELECT id FROM icao_regions WHERE region_code = 'Y'), 'YB', 'Australia', 'Queensland and nearby areas'),
((SELECT id FROM icao_regions WHERE region_code = 'Z'), 'ZB', 'China', 'North China')
ON DUPLICATE KEY UPDATE
  icao_region_id = VALUES(icao_region_id),
  country_name = VALUES(country_name),
  area_name = VALUES(area_name),
  is_active = TRUE;
