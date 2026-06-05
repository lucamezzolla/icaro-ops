# Staff and Routes table/dialog redesign

This patch redesigns Staff and Routes to follow the Flight Log interaction model.

## Files

```text
staff.html
routes.html
src/css/staff.css
src/css/routes.css
src/js/staff.js
src/js/routes.js
api/public/staff/detail.php
api/public/routes/detail.php
api/public/routes/preview.php
docs/STAFF_ROUTES_TABLE_DIALOGS.md
```

## Apply

```bash
cd /home/luca/Documenti/html/icaro-ops
unzip -o /home/luca/Scaricati/icaro-ops-staff-routes-table-dialogs-patch.zip
```

## Routes

Compact table:

```text
Route
Departure UTC
Aircraft
Crew
Duration
Ticket
Status
Actions
```

Add Route opens a dialog.

The dialog includes a dedicated economic preview:

```text
distance
duration
aircraft
capacity
low/expected/high passenger revenue
fuel cost
maintenance cost
staff cost
expected profit
break-even passengers
recommendation
```

## Staff

Compact table:

```text
Name
Role
Status
Reliability
Fatigue
Cost/flight
Details
```

Details dialog shows full staff data and licenses.

Add Staff opens a hiring dialog using the existing candidates/hire endpoints.
