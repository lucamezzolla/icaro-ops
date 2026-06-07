# Active detail pilot columns fix

## Problem

The map popup returned 500:

```text
Unknown column 'sfi.pilot_1_staff_id'
```

because `api/public/flights/active-detail.php` assumed fixed pilot column names that are not present in your current database.

## Apply

```bash
cd /home/luca/Documenti/html/icaro-ops
unzip -o /home/luca/Scaricati/icaro-ops-active-detail-pilot-columns-fix-patch.zip

php -l api/public/flights/active-detail.php
```

Then refresh:

```text
Ctrl + F5
```

## What changes

`active-detail.php` now detects which columns actually exist in:

```text
scheduled_flight_instances
```

It supports several possible names, for example:

```text
pilot_1_staff_id
captain_staff_id
primary_pilot_staff_id
pilot_staff_id

pilot_2_staff_id
first_officer_staff_id
secondary_pilot_staff_id
copilot_staff_id

technician_staff_id
maintenance_staff_id
```

If no matching crew columns exist, it returns `null`/`-` for crew instead of crashing.

The map popup should still show:

```text
speed
timer
route
progress
arrival UTC
```
