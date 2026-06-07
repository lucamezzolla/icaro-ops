# Passenger capacity and single-aircraft dispatch fix

## Problem 1

Starting a flight failed with:

```text
SQLSTATE[HY000]: General error: 1364 Field 'passenger_capacity' doesn't have a default value
```

The table `scheduled_flight_instances` requires `passenger_capacity`, but the dispatch insert was only setting `passenger_count`.

## Problem 2

For non-scheduled flights, the UI asked you to choose an aircraft even when there was only one compatible available aircraft.

## Apply

```bash
cd /home/luca/Documenti/html/icaro-ops
unzip -o /home/luca/Scaricati/icaro-ops-passenger-capacity-and-auto-single-aircraft-patch.zip

python3 docs/patch_start_flight_passenger_capacity.py
python3 docs/patch_routes_auto_select_single_aircraft.py

php -l api/public/flights/start-service-now.php
```

Refresh:

```text
Ctrl + F5
```

## Result

Flight instance insert now sets:

```text
passenger_capacity = aircraft passenger capacity
passenger_count    = estimated passengers on board
```

For non-scheduled flights:

```text
0 available aircraft  -> cannot depart
1 available aircraft  -> auto-selected, no choice dialog
2+ available aircraft -> choice dialog
```
