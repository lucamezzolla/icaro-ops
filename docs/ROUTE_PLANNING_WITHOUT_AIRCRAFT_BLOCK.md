# Route planning without aircraft block

A route is now treated as a planning/commercial object.

It can be created even if the aircraft is:

- in flight
- at another airport
- broken
- in maintenance
- not yet assigned

Operational checks remain at dispatch/start-flight time.

## Apply

```bash
cd /home/luca/Documenti/html/icaro-ops
unzip -o /home/luca/Scaricati/icaro-ops-route-planning-no-aircraft-block-patch.zip
sudo mysql icaro_ops < db/mysql/077_route_planning_without_aircraft_block.sql
```

## Gameplay direction

Later, when dispatch is blocked, the game should create mailbox events such as:

```text
DISPATCH_BLOCKED
AIRCRAFT_MAINTENANCE_REQUIRED
AIRCRAFT_BROKEN
CREW_UNAVAILABLE
```

The player can then choose:

```text
substitute aircraft
delay flight
repair aircraft
cancel flight
```

Canceling should affect reputation and budget.
