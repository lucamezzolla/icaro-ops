# Active flight clickable enhancer

## Problem

The active-flight timer existed, but clicking the aircraft did nothing because the UI element did not have:

```html
data-aircraft-id
```

or:

```html
data-flight-instance-id
```

## Apply

```bash
cd /home/luca/Documenti/html/icaro-ops
unzip -o /home/luca/Scaricati/icaro-ops-active-flight-clickable-enhancer-patch.zip

python3 docs/patch_include_active_flight_clickable_enhancer.py
cat docs/active_flight_clickable_enhancer_css_append.css >> src/css/fleet.css
cat docs/active_flight_clickable_enhancer_css_append.css >> src/css/routes.css

php -l api/public/flights/active-list.php
```

Refresh:

```text
Ctrl + F5
```

## What it adds

New endpoint:

```text
api/public/flights/active-list.php
```

New script:

```text
src/js/active-flight-clickable-enhancer.js
```

It does two things:

```text
1. Shows a small "Active flights" panel with active aircraft.
2. Scans the current page for rows/cards containing the aircraft registration code and makes them clickable.
```

Clicking opens the live flight dialog with:

```text
- speed
- remaining time
- progress
- UTC departure/arrival
- crew
- passengers
```

The remaining time updates every second.
