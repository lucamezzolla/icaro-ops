# Route / Service / Flight dispatch foundation

This patch starts the architectural split:

```text
air_routes                 = abstract network routes
scheduled_services         = scheduled commercial offer over a route
scheduled_flight_instances = actual operational flights
```

## Key design

Routes do **not** permanently contain aircraft, crew or ticket values.

A flight has operational requirements. At departure time, dispatch chooses a compatible aircraft available at the origin airport.

Example:

```text
Scheduled flight LIRA -> LIBP requires LIGHT_COMMERCIAL.

If IO-001 is away on an extra flight, IO-002 Cessna 208B can fly it instead.
If no compatible aircraft is at LIRA, the flight can be delayed/cancelled with penalties.
```

## Apply

```bash
cd /home/luca/Documenti/html/icaro-ops
unzip -o /home/luca/Scaricati/icaro-ops-route-service-dispatch-foundation-patch.zip
sudo mysql icaro_ops < db/mysql/090_route_service_dispatch_foundation.sql
python3 docs/patch_signup_no_logo_initial_budget.py
```

## Reset

The reset endpoint is replaced:

```text
api/public/dev/reset-my-data.php
```

It now deletes company/player data plus:

```text
fleet
staff
staff candidate market
legacy routes
scheduled services
flight instances
new dispatch requirements
mailbox
maintenance events
reputation journal
```

Confirmation string stays:

```text
RESET_MY_ICARO_OPS_DATA
```

## Signup

The signup page should no longer expose company logo. Logo should move later to Settings.

Initial budget is raised to:

```text
8,500,000 EUR
```

This is intended for:

```text
2 Cessna 208B
pilots
technicians
early route testing
```

## Helper

```text
api/lib/dispatch-aircraft.php
```

Provides:

```text
find_compatible_aircraft_for_flight()
dispatch_flight_aircraft()
```

Current early-game compatibility prevents absurd dispatch, such as Concorde on small light-commercial routes.

## Next step

Wire scheduled-flight start and future extra-flight preview/start endpoints to the dispatch helper.
