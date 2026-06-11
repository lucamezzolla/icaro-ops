# Flight Log pagination

This patch adds classic pagination to the Flight Log.

## Changes

- Backend query now returns 10 records per page.
- Records are ordered newest to oldest:

```sql
ORDER BY COALESCE(actual_departure_at_utc, scheduled_departure_at_utc) DESC, id DESC
```

- Pagination metadata is returned by the API.
- Pagination controls are shown above and below the table.
- Controls: First, Previous, Next, Last.

## Apply

From the project root:

```bash
unzip -o /home/luca/Scaricati/icaro-ops-flight-log-pagination-patch.zip
python3 docs/patch_flight_log_pagination.py

php -l api/public/flights/log.php
node --check src/js/flight-log.js
```

Then hard-refresh the Flight Log page.

## Rollback

```bash
git restore flight-log.html src/js/flight-log.js src/css/flight-log.css api/public/flights/log.php
rm -f docs/patch_flight_log_pagination.py docs/FLIGHT_LOG_PAGINATION.md
```

## Commit

```bash
git add flight-log.html src/js/flight-log.js src/css/flight-log.css api/public/flights/log.php
git add docs/patch_flight_log_pagination.py docs/FLIGHT_LOG_PAGINATION.md
git commit -m "Add flight log pagination"
git push origin development
```
