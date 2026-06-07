# Staff candidates PDO and model search fix

Fixes the Staff candidate API after the fleet-aware hiring patch.

## Fixed

- Avoids reusing the same PDO named placeholders multiple times in the same SQL statement.
- Fixes `SQLSTATE[HY093]: Invalid parameter number` on filtered searches.
- Keeps the fleet-only matching logic, but uses separate placeholders for the `EXISTS` filter and the `LEFT JOIN` aggregation.
- Makes text search match type rating metadata too, so queries such as `dougl` can match pilots generated for aircraft models whose type rating description contains `Douglas`.
- Updates existing staff license type metadata with `ON DUPLICATE KEY UPDATE`, so generated type ratings get refreshed descriptions.

## Validation

```bash
php -l api/public/staff/candidates.php
```

Recommended browser/API checks:

```bash
curl 'http://localhost:8080/api/public/staff/candidates.php?role=PILOT&q=&fleetOnly=1'
curl 'http://localhost:8080/api/public/staff/candidates.php?role=PILOT&q=dougl&fleetOnly=1'
curl 'http://localhost:8080/api/public/staff/candidates.php?role=PILOT&q=MD82&fleetOnly=1'
```
