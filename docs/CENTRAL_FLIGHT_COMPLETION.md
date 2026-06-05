# Central flight completion

This patch centralizes flight completion logic.

## Why

Before this patch, `complete_due_flights()` existed in multiple files:

```text
api/public/flights/active.php
api/public/flights/start-scheduled.php
api/public/dispatch/process-due-routes.php
```

That caused partial updates depending on which endpoint completed a flight.

## New single source

```text
api/lib/flight-completion.php
```

It completes due flights and always applies:

```text
- flight status COMPLETED
- aircraft AVAILABLE at destination
- budget update
- reputation update
- aircraft wear: hours/cycles/condition
- mailbox/event if maintenance threshold is reached
```

## Apply

```bash
cd /home/luca/Documenti/html/icaro-ops
unzip -o /home/luca/Scaricati/icaro-ops-central-flight-completion-patch.zip
python3 docs/patch_central_flight_completion.py
```

Then check PHP syntax:

```bash
php -l api/lib/flight-completion.php
php -l api/public/flights/active.php
php -l api/public/flights/start-scheduled.php
php -l api/public/dispatch/process-due-routes.php
```

## Test

Start PHP server, then call active flights:

```bash
curl "http://127.0.0.1:8080/api/public/flights/active.php"
```

After a flight arrives, check:

```bash
sudo mysql icaro_ops -e "
SELECT id, flight_code, status, profit_amount
FROM scheduled_flight_instances
ORDER BY id DESC
LIMIT 5;

SELECT registration_code, status, current_airport_icao_code, condition_percent, airframe_hours, cycles_count
FROM company_aircraft;

SELECT event_code, reputation_before, reputation_delta, reputation_after, reason
FROM reputation_journal
ORDER BY id DESC
LIMIT 10;
"
```
