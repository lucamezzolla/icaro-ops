-- Icaro Ops - Reputation journal rule for missed scheduled flights
-- Makes the missed scheduled flight reputation penalty traceable in reputation_journal.

INSERT INTO reputation_rules (
  event_code,
  description,
  reputation_delta,
  min_reputation,
  max_reputation,
  is_active
) VALUES (
  'MISSED_SCHEDULED_FLIGHT_PENALTY',
  'A scheduled flight was missed because no compatible available aircraft was present at the origin airport.',
  -10,
  0,
  100,
  1
)
ON DUPLICATE KEY UPDATE
  description = VALUES(description),
  reputation_delta = VALUES(reputation_delta),
  min_reputation = VALUES(min_reputation),
  max_reputation = VALUES(max_reputation),
  is_active = VALUES(is_active);

SELECT
  event_code,
  description,
  reputation_delta,
  min_reputation,
  max_reputation,
  is_active
FROM reputation_rules
WHERE event_code = 'MISSED_SCHEDULED_FLIGHT_PENALTY';
