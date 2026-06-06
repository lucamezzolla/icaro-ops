# Flight codes and compatibility foundation

## Apply

```bash
cd /home/luca/Documenti/html/icaro-ops
unzip -o /home/luca/Scaricati/icaro-ops-flight-codes-compatibility-patch.zip

sudo mysql icaro_ops < db/mysql/095_flight_route_public_codes.sql

python3 docs/patch_start_flight_epoch_code.py
python3 docs/patch_flights_category_explanation_js.py
python3 docs/patch_flights_category_explanation_html.py
```

Refresh:

```text
Ctrl + F5
```

## Flight instance code

Real operational flights now use:

```text
IO-<epoch>
```

Example:

```text
IO-1780758422
```

This is the code that should appear in Flight Log.

## Flight route public code

Abstract flight routes get codes like:

```text
DOM-0001
INT-0001
CHT-0001
HEL-0001
CGO-0001
MIL-0001
RES-0001
TRN-0001
POS-0001
```

## Aircraft compatibility

New helper:

```text
api/lib/flight-route-compatibility.php
```

It centralizes:

```text
route category detection
route public code generation
compatible airplane model selection
ICAO airplane code list
```

For now the compatibility logic is still early-game, but no longer lives as a hardcoded string inside create.php.
