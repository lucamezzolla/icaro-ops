# Manual aircraft selection for flights

## Apply

```bash
cd /home/luca/Documenti/html/icaro-ops
unzip -o /home/luca/Scaricati/icaro-ops-manual-aircraft-selection-patch.zip

python3 docs/patch_flights_manual_aircraft_js.py
python3 docs/patch_flights_manual_aircraft_html.py
python3 docs/patch_dispatch_manual_model_codes.py
python3 docs/patch_start_flight_manual_model_codes.py
cat docs/manual_aircraft_selection_css_append.css >> src/css/routes.css
```

Refresh:

```text
Ctrl + F5
```

## What changes

Create flight no longer auto-selects theoretical airplanes.

The dialog now loads airplane models from your owned fleet and lets you choose one or more models manually.

Example:

```text
C208 - Cessna 208B Grand Caravan EX
PC12 - Pilatus PC-12 NGX
```

The selected models are stored in:

```text
scheduled_services.compatible_aircraft_model_codes
```

At `Start flight now`, dispatch searches only among real owned aircraft whose model code was selected for that flight.

## Unlocking more airplanes

To make another airplane available in the selector:

```text
1. Go to Fleet
2. Buy that aircraft model
3. Return to Flights
4. Add flight
5. The newly owned model appears in the Airplanes for this flight list
```

No aircraft = not selectable.
