# Aircraft delivery airport selection

## Apply

```bash
cd /home/luca/Documenti/html/icaro-ops
unzip -o /home/luca/Scaricati/icaro-ops-aircraft-delivery-airport-patch.zip

python3 docs/patch_fleet_buy_delivery_airport.py
cat docs/delivery_airport_dialog_css_append.css >> src/css/fleet.css
```

Refresh:

```text
Ctrl + F5
```

## What changes

When buying an aircraft:

```text
1. Click Buy
2. Choose delivery airport
3. Confirm purchase
4. Aircraft is created as AVAILABLE at that airport
```

The selected airport becomes:

```text
home_base_icao_code
current_airport_icao_code
```

for the newly purchased aircraft.

## New endpoint

```text
api/public/airports/search.php
```

Searches by:

```text
ICAO
IATA
city
airport name
```
