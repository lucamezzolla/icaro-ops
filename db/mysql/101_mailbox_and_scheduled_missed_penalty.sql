USE icaro_ops;

START TRANSACTION;

CREATE TABLE IF NOT EXISTS company_mailbox_messages (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  company_id BIGINT UNSIGNED NOT NULL,
  message_type VARCHAR(60) NOT NULL,
  severity VARCHAR(30) NOT NULL DEFAULT 'INFO',
  title VARCHAR(180) NOT NULL,
  body TEXT NOT NULL,
  related_entity_type VARCHAR(60) NULL,
  related_entity_id BIGINT UNSIGNED NULL,
  is_read TINYINT(1) NOT NULL DEFAULT 0,
  created_at_utc TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_company_mailbox_company_read_created (company_id, is_read, created_at_utc),
  INDEX idx_company_mailbox_related (related_entity_type, related_entity_id)
);

CREATE TABLE IF NOT EXISTS company_financial_events (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  company_id BIGINT UNSIGNED NOT NULL,
  event_type VARCHAR(80) NOT NULL,
  amount DECIMAL(14,2) NOT NULL DEFAULT 0.00,
  currency_code CHAR(3) NOT NULL DEFAULT 'EUR',
  description TEXT NULL,
  related_entity_type VARCHAR(60) NULL,
  related_entity_id BIGINT UNSIGNED NULL,
  created_at_utc TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_company_financial_events_company_created (company_id, created_at_utc),
  INDEX idx_company_financial_events_related (related_entity_type, related_entity_id)
);

COMMIT;

SHOW TABLES LIKE 'company_mailbox_messages';
SHOW TABLES LIKE 'company_financial_events';
