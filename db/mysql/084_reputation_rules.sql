-- Icaro Ops reputation rules.
USE icaro_ops;

START TRANSACTION;

CREATE TABLE IF NOT EXISTS reputation_rules (
  event_code VARCHAR(80) NOT NULL,
  description VARCHAR(500) NOT NULL,
  reputation_delta INT NOT NULL DEFAULT 0,
  min_reputation INT NOT NULL DEFAULT 0,
  max_reputation INT NOT NULL DEFAULT 100,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  updated_at_utc TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (event_code),
  CONSTRAINT chk_reputation_rules_bounds
    CHECK (
      min_reputation >= 0
      AND max_reputation <= 100
      AND min_reputation <= max_reputation
    )
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS reputation_journal (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  company_id BIGINT UNSIGNED NOT NULL,
  event_code VARCHAR(80) NOT NULL,
  reputation_before INT NOT NULL,
  reputation_delta INT NOT NULL,
  reputation_after INT NOT NULL,
  related_entity_type VARCHAR(50) NULL,
  related_entity_id BIGINT UNSIGNED NULL,
  reason VARCHAR(500) NOT NULL,
  created_at_utc TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_reputation_journal_company_time (company_id, created_at_utc),
  KEY idx_reputation_journal_event (event_code),
  CONSTRAINT fk_reputation_journal_company
    FOREIGN KEY (company_id)
    REFERENCES companies(id)
    ON UPDATE CASCADE
    ON DELETE CASCADE,
  CONSTRAINT fk_reputation_journal_rule
    FOREIGN KEY (event_code)
    REFERENCES reputation_rules(event_code)
    ON UPDATE CASCADE
    ON DELETE RESTRICT,
  CONSTRAINT chk_reputation_journal_values
    CHECK (
      reputation_before BETWEEN 0 AND 100
      AND reputation_after BETWEEN 0 AND 100
    )
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO reputation_rules (
  event_code,
  description,
  reputation_delta,
  min_reputation,
  max_reputation,
  is_active
) VALUES
('FLIGHT_COMPLETED_PROFITABLE', 'A scheduled flight completed successfully with positive profit.', 1, 0, 100, TRUE),
('FLIGHT_COMPLETED_BREAK_EVEN_OR_LOSS', 'A scheduled flight completed without operational problems but did not generate positive profit.', 0, 0, 100, TRUE),
('DISPATCH_STARTED_PRIMARY', 'A scheduled flight departed with its primary aircraft.', 0, 0, 100, TRUE),
('DISPATCH_STARTED_BACKUP', 'A scheduled flight departed with a backup aircraft. No penalty because the service was preserved.', 0, 0, 100, TRUE),
('DISPATCH_CANCELLED_NO_AIRCRAFT', 'A scheduled flight could not depart because no aircraft was available at origin.', -8, 0, 100, TRUE),
('DISPATCH_BLOCKED_CREW', 'A scheduled flight could not depart because assigned pilots were unavailable or unqualified.', -4, 0, 100, TRUE),
('DISPATCH_BLOCKED_MAINTENANCE', 'A scheduled flight could not depart because the aircraft was not fit for service.', -6, 0, 100, TRUE),
('MAINTENANCE_DELAY_ACCEPTED', 'Maintenance was scheduled despite a known delay risk.', -1, 0, 100, TRUE),
('MAINTENANCE_COMPLETED', 'Maintenance completed successfully.', 0, 0, 100, TRUE)
ON DUPLICATE KEY UPDATE
  description = VALUES(description),
  reputation_delta = VALUES(reputation_delta),
  min_reputation = VALUES(min_reputation),
  max_reputation = VALUES(max_reputation),
  is_active = VALUES(is_active);

ALTER TABLE companies
  MODIFY reputation_score INT NOT NULL DEFAULT 100;

UPDATE companies
SET reputation_score = 100
WHERE reputation_score IS NULL;

CREATE OR REPLACE VIEW v_reputation_journal AS
SELECT
  j.id AS journal_id,
  j.company_id,
  co.company_name,
  j.event_code,
  r.description,
  j.reputation_before,
  j.reputation_delta,
  j.reputation_after,
  j.related_entity_type,
  j.related_entity_id,
  j.reason,
  j.created_at_utc
FROM reputation_journal j
JOIN companies co
  ON co.id = j.company_id
JOIN reputation_rules r
  ON r.event_code = j.event_code;

COMMIT;
