# Fix missing flight_date_utc on flight start

## Problem

Starting a flight failed with:

```text
SQLSTATE[HY000]: General error: 1364 Field 'flight_date_utc' doesn't have a default value
```

The table `scheduled_flight_instances` requires `flight_date_utc`, but `api/public/flights/start-service-now.php` did not include it in the insert.

## Apply

```bash
cd /home/luca/Documenti/html/icaro-ops
unzip -o /home/luca/Scaricati/icaro-ops-flight-date-utc-fix-patch.zip

python3 docs/patch_start_flight_date_utc.py
php -l api/public/flights/start-service-now.php
```

Then try `Start flight now` again.

## Change

The flight instance insert now sets:

```text
flight_date_utc = gmdate('Y-m-d')
```

so the value is always based on UTC, consistent with aviation logic.
