# Route edit and delete

This patch adds route editing and deletion.

## Files

```text
api/public/routes/update.php
api/public/routes/delete.php
src/js/routes.js
docs/ROUTE_EDIT_DELETE.md
```

## Apply

```bash
cd /home/luca/Documenti/html/icaro-ops
unzip -o /home/luca/Scaricati/icaro-ops-route-edit-delete-patch.zip
```

No SQL is required.

## Behavior

### Edit route

The route form becomes edit mode.

Editable fields:

```text
origin ICAO
destination ICAO
scheduled UTC time
ticket price
```

The backend recalculates:

```text
distance
duration
range check
```

A route cannot be edited while it has active/scheduled flights:

```text
SCHEDULED
IN_FLIGHT
```

### Delete route

If the route has no flight history:

```text
DELETE FROM company_routes
```

If the route has completed/historical flights:

```text
status = CANCELLED
auto_dispatch_enabled = FALSE
```

A route cannot be deleted while it has active/scheduled flights.
