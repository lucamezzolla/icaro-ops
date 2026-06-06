# Start scheduled service as a real flight

This patch adds the missing transition from Scheduled Service to real Flight Instance.

## Apply

```bash
cd /home/luca/Documenti/html/icaro-ops
unzip -o /home/luca/Scaricati/icaro-ops-start-service-flight-patch.zip

sudo mysql icaro_ops < db/mysql/091_service_flight_start_foundation.sql

python3 docs/patch_routes_start_service_flight.py
python3 docs/patch_routes_wording_services.py
```

Refresh:

```text
Ctrl + F5
```

Each scheduled service gets:

```text
Start flight now
```

The endpoint creates a real `scheduled_flight_instances` row, assigns a compatible aircraft at the origin, assigns two C208 pilots, and marks the flight `IN_FLIGHT`.
