USE icaro_ops;

ALTER TABLE companies
  MODIFY reputation_score INT NOT NULL DEFAULT 100;

UPDATE companies
SET reputation_score = 100
WHERE reputation_score IS NULL
   OR reputation_score = 0;

SELECT
  id,
  company_name,
  reputation_score
FROM companies;
