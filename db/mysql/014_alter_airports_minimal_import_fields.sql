-- Icaro Ops airport import fields.
-- Keep airports compact: add only fields that are repeatedly useful for gameplay/imports.

USE icaro_ops;

ALTER TABLE airports
  ADD COLUMN IF NOT EXISTS service_category ENUM(
    'INTERNATIONAL',
    'NATIONAL',
    'MILITARY',
    'OTHER',
    'UNKNOWN'
  ) NOT NULL DEFAULT 'UNKNOWN' AFTER airport_type,
  ADD COLUMN IF NOT EXISTS aip_url VARCHAR(500) NULL AFTER operator_country_name,
  ADD COLUMN IF NOT EXISTS chart_url VARCHAR(500) NULL AFTER aip_url,
  ADD COLUMN IF NOT EXISTS source_rating_percent DECIMAL(5,2) NULL AFTER chart_url;

CREATE INDEX IF NOT EXISTS idx_airports_service_category
  ON airports(service_category);
