-- Airport runway source notes.
-- Kept outside airports to avoid bloating the primary airport table.
-- This stores raw runway information from source PDFs until we normalize runways later.

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
