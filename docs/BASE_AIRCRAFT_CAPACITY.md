# Base aircraft capacity

This patch adds aircraft-capacity data to airport bases.

## Difference from base slots

Airport base slots answer:

```text
How many companies can have a base at this airport?
```

Aircraft capacity answers:

```text
How many aircraft can each base manage or park?
```

## Added fields

`airport_capacity_profiles` gets:

```text
max_aircraft_per_player_base
max_aircraft_per_rival_base
max_aircraft_on_ground_per_base
```

## Global first-pass capacity rules

```text
AIRSTRIP    managed 2,  on ground 1
SMALL       managed 4,  on ground 2
MEDIUM      managed 6,  on ground 4
REGIONAL    managed 12, on ground 8
HUB         managed 30, on ground 20
```

## LIRA / Rome Ciampino

Ciampino remains:

```text
max_total_bases = 2
```

and now also gets:

```text
max_aircraft_per_player_base = 6
max_aircraft_per_rival_base = 6
max_aircraft_on_ground_per_base = 4
```

## Views

```text
v_player_base_aircraft_capacity_status
v_rival_base_aircraft_capacity_status
```

These views calculate:

```text
aircraft_owned_count
aircraft_at_base_count
aircraft_in_flight_count
aircraft_maintenance_count
free_managed_aircraft_slots
free_ground_aircraft_slots
```

## Rival aircraft

The patch creates:

```text
rival_company_aircraft
```

and seeds one test aircraft for Aurelia Air Services at LIRA, if the model and rival company exist.

## Apply

```bash
cd /home/luca/Documenti/html/icaro-ops
unzip -o /home/luca/Scaricati/icaro-ops-base-aircraft-capacity-patch.zip
sudo mysql icaro_ops < db/mysql/068_base_aircraft_capacity.sql
```

## Test

```bash
sudo mysql icaro_ops -e "
SELECT *
FROM v_player_base_aircraft_capacity_status
WHERE airport_icao_code = 'LIRA';
"
```

```bash
sudo mysql icaro_ops -e "
SELECT *
FROM v_rival_base_aircraft_capacity_status
WHERE airport_icao_code = 'LIRA';
"
```

Then open:

```text
http://127.0.0.1:8080/index.html?companyId=1
```

Click bases to see aircraft capacity in the left panel.
