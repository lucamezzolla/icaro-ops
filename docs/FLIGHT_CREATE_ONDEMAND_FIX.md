# Fix on-demand flight creation default

## Apply

```bash
cd /home/luca/Documenti/html/icaro-ops
unzip -o /home/luca/Scaricati/icaro-ops-flight-create-ondemand-fix-patch.zip

python3 docs/patch_flights_ondemand_default.py
python3 docs/patch_flights_html_ondemand_default.py
```

Refresh:

```text
Ctrl + F5
```

## Changes

The create dialog now defaults to:

```text
ON_DEMAND
```

and the scheduled time starts:

```text
empty
disabled
not required
```

When `ON_DEMAND` is submitted, the payload sends:

```text
scheduled_departure_time_utc = ""
```

and the backend forces:

```text
scheduled_departure_time_utc = NULL
```

even if a stale value such as `10:00` reaches the API.

The page title becomes simply:

```text
Flights
```

## DB naming note

The DB still contains legacy names like:

```text
air_routes
scheduled_services
company_routes
```

This is intentional for now. Renaming those tables physically would be a large destructive migration while we are still stabilizing the model.

Recommended staged approach:

```text
Now:
  UI says Flights.
  API creates flight-oriented records over existing service/route foundation.

Later:
  add compatibility views or aliases.

Final:
  rename tables only when the model is stable.
```
