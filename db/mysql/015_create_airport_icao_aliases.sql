-- Airport ICAO aliases.
-- Used for cases where a source lists multiple ICAO codes for one airport.
-- Example: Western Sahara entries may list GSxx / GMxx.

USE icaro_ops;

CREATE TABLE IF NOT EXISTS airport_icao_aliases (
  airport_icao_code CHAR(4) NOT NULL,
  alias_icao_code CHAR(4) NOT NULL,
  notes VARCHAR(255) NULL,
  created_at_utc TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

  PRIMARY KEY (airport_icao_code, alias_icao_code),
  UNIQUE KEY uk_airport_icao_aliases_alias (alias_icao_code),

  CONSTRAINT fk_airport_icao_aliases_airport
    FOREIGN KEY (airport_icao_code)
    REFERENCES airports(icao_code)
    ON UPDATE CASCADE
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
