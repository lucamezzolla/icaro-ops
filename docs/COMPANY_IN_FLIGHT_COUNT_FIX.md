# Company panel in-flight count fix

The Company panel showed:

```text
In flight: 2
```

while the database had:

```text
company_aircraft.status = IN_FLIGHT => 4
scheduled_flight_instances.status = IN_FLIGHT => 4
```

## Cause

`api/public/company/current.php` was reading `aircraft_in_flight_count` from:

```text
v_player_base_aircraft_capacity_status
```

joined only to the current base airport.

That value is base/capacity scoped, not the global company fleet count.

## Fix

The endpoint now counts all company aircraft currently in flight:

```sql
SELECT COUNT(*)
FROM company_aircraft
WHERE company_id = co.id
  AND status = 'IN_FLIGHT'
```

## Apply

From the project root:

```bash
unzip -o /home/luca/Scaricati/icaro-ops-company-in-flight-count-patch.zip
python3 docs/patch_company_in_flight_count.py

php -l api/public/company/current.php
```

Then hard-refresh the Company panel.

## Rollback

```bash
git restore api/public/company/current.php
rm -f docs/patch_company_in_flight_count.py docs/COMPANY_IN_FLIGHT_COUNT_FIX.md
```

## Commit

```bash
git add api/public/company/current.php docs/patch_company_in_flight_count.py docs/COMPANY_IN_FLIGHT_COUNT_FIX.md
git commit -m "Fix company in-flight aircraft count"
git push origin development
```
