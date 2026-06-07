# Concorde type rating and active flight timer

## Apply

```bash
cd /home/luca/Documenti/html/icaro-ops
unzip -o /home/luca/Scaricati/icaro-ops-concorde-rating-and-flight-timer-patch.zip

python3 docs/patch_dispatch_generic_aircraft_type_rating.py
python3 docs/patch_include_active_flight_timer_script.py
cat docs/active_flight_timer_css_append.css >> src/css/routes.css
cat docs/active_flight_timer_css_append.css >> src/css/fleet.css

php -l api/lib/aircraft-type-rating.php
php -l api/lib/flight-dispatch-selection.php
php -l api/public/flights/active-detail.php
```

Refresh:

```text
Ctrl + F5
```

## Concorde pilot rating

The dispatch code no longer treats unknown aircraft models as CPL-only.

It now uses:

```text
required license = ICAO_TYPE_CODE + "_TYPE"
```

Examples:

```text
CONC -> CONC_TYPE
A320 -> A320_TYPE
B738 -> B738_TYPE
```

So a Concorde flight requires:

```text
2 active pilots with CPL + CONC_TYPE
```

## Check Concorde pilots

```bash
sudo mysql icaro_ops -e "
SELECT
  s.id,
  s.display_name,
  GROUP_CONCAT(l.license_code ORDER BY l.license_code SEPARATOR ', ') AS licenses
FROM company_staff s
LEFT JOIN company_staff_licenses l
  ON l.company_staff_id = s.id
WHERE s.company_id = 1
  AND s.staff_role = 'PILOT'
GROUP BY s.id, s.display_name
HAVING licenses LIKE '%CONC_TYPE%';
"
```

## Active aircraft timer

New endpoint:

```text
api/public/flights/active-detail.php
```

New JS:

```text
src/js/active-flight-timer-dialog.js
```

It opens a dialog when clicking an element with:

```html
data-flight-instance-id="123"
```

or:

```html
data-aircraft-id="45"
```

The dialog shows aircraft speed and a remaining-time timer updated every second.
