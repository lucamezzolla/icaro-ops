-- Icaro Ops - Make missed scheduled flight mailbox messages visible
-- Older helper messages were written to company_mailbox_messages, while the UI reads game_mailbox_messages.
-- This migration copies existing missed scheduled flight messages into the visible mailbox table.

INSERT INTO game_mailbox_messages (
  company_id,
  message_type,
  severity,
  status,
  title,
  body,
  related_entity_type,
  related_entity_id,
  created_at_utc
)
SELECT
  cmm.company_id,
  'DISPATCH_BLOCKED',
  CASE
    WHEN cmm.severity IN ('INFO', 'WARNING', 'CRITICAL') THEN cmm.severity
    ELSE 'WARNING'
  END,
  CASE WHEN cmm.is_read = 1 THEN 'READ' ELSE 'UNREAD' END,
  cmm.title,
  cmm.body,
  cmm.related_entity_type,
  cmm.related_entity_id,
  cmm.created_at_utc
FROM company_mailbox_messages cmm
WHERE cmm.message_type IN ('MISSED_SCHEDULED_FLIGHT', 'SCHEDULED_FLIGHT_MISSED')
  AND NOT EXISTS (
    SELECT 1
    FROM game_mailbox_messages gmm
    WHERE gmm.company_id = cmm.company_id
      AND gmm.related_entity_type <=> cmm.related_entity_type
      AND gmm.related_entity_id <=> cmm.related_entity_id
      AND gmm.title = cmm.title
      AND gmm.body = cmm.body
  );

SELECT
  COUNT(*) AS visible_missed_scheduled_messages
FROM game_mailbox_messages
WHERE message_type = 'DISPATCH_BLOCKED'
  AND title LIKE '%Scheduled flight%';
