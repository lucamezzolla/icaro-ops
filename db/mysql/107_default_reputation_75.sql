USE icaro_ops;

START TRANSACTION;

/*
 * Default reputation rule.
 *
 * A newly registered company should start with a neutral-good reputation:
 *
 * reputation_score = 75 / 100
 *
 * This migration:
 * - fixes current local development company reputation
 * - changes the default value for future companies if the column exists
 */

SET @has_reputation_score := (
  SELECT COUNT(*)
  FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'companies'
    AND COLUMN_NAME = 'reputation_score'
);

SET @sql := IF(
  @has_reputation_score > 0,
  'ALTER TABLE companies MODIFY reputation_score TINYINT UNSIGNED NOT NULL DEFAULT 75',
  'SELECT ''companies.reputation_score not found; skipping ALTER'' AS warning_message'
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

/*
 * Current local/dev company reset.
 * This affects the existing company/account now.
 */
UPDATE companies
SET reputation_score = 75
WHERE reputation_score IS NULL
   OR reputation_score <> 75;

/*
 * Safety clamp for future accidental out-of-range values.
 */
UPDATE companies
SET reputation_score = LEAST(100, GREATEST(0, reputation_score))
WHERE reputation_score IS NOT NULL;

COMMIT;

SELECT
  id,
  company_name,
  reputation_score
FROM companies
ORDER BY id;
