# Staff operational status

This patch adds a separate operational status for staff.

It does not change `employment_status`.

## New meaning

```text
employment_status = ACTIVE / DISMISSED / ...
operational_status = AVAILABLE / IN_FLIGHT
```

Pilots and technicians become `IN_FLIGHT` when they are assigned to an `IN_FLIGHT` record in `scheduled_flight_instances`.

## Important DB change

Your current `scheduled_flight_instances` table has no staff assignment columns, so the game cannot know which pilots are busy.

This patch adds:

```text
pilot_1_staff_id
pilot_2_staff_id
technician_staff_id
```

The current dispatch code already tries to write these fields dynamically. Once the columns exist, future flights will persist the crew.

## Apply

From the project root:

```bash
unzip -o /home/luca/Scaricati/icaro-ops-staff-operational-status-patch.zip
python3 docs/patch_staff_operational_status.py

sudo mysql icaro_ops < db/mysql/patch_staff_operational_status.sql

php -l api/public/staff/list.php
php -l api/public/staff/my-staff.php
node --check src/js/staff.js
```

Then start or wait for a scheduled flight and refresh Staff.

## Notes

Already-running old flights may not have crew IDs saved, because the columns did not exist at the time they were created. New flights should show assigned pilots as `IN_FLIGHT / BUSY`.

## Rollback

```bash
git restore api/public/staff/list.php api/public/staff/my-staff.php src/js/staff.js
rm -f db/mysql/patch_staff_operational_status.sql
rm -f docs/patch_staff_operational_status.py docs/STAFF_OPERATIONAL_STATUS.md
```

The SQL rollback is intentionally not automatic. If needed:

```sql
ALTER TABLE scheduled_flight_instances
  DROP COLUMN pilot_1_staff_id,
  DROP COLUMN pilot_2_staff_id,
  DROP COLUMN technician_staff_id;
```

## Commit

```bash
git add api/public/staff/list.php api/public/staff/my-staff.php src/js/staff.js
git add db/mysql/patch_staff_operational_status.sql
git add docs/patch_staff_operational_status.py docs/STAFF_OPERATIONAL_STATUS.md
git commit -m "Add staff operational availability status"
git push origin development
```
