# Flights airplane filter ICAO-only

This patch changes the Flights Airplane filter so it filters only by aircraft ICAO type code.

## Behavior

The filter uses only:

```text
compatible_aircraft_icao_codes
icao_type_code
```

It ignores:

```text
manufacturer
model_name
preferred_aircraft_model_name
internal model codes
```

## Examples

```text
A      -> A320 / A321 / A333...
A320   -> A320 only
C      -> CONC
CONC   -> CONC
```

## Apply

From the project root:

```bash
unzip -o /home/luca/Scaricati/icaro-ops-flights-airplane-filter-icao-only-patch.zip
python3 docs/patch_flights_airplane_filter_icao_only.py

node --check src/js/routes.js
```

Then hard-refresh the Flights page.

## Rollback

```bash
git restore src/js/routes.js
rm -f docs/patch_flights_airplane_filter_icao_only.py docs/FLIGHTS_AIRPLANE_FILTER_ICAO_ONLY.md
```

## Commit

```bash
git add src/js/routes.js docs/patch_flights_airplane_filter_icao_only.py docs/FLIGHTS_AIRPLANE_FILTER_ICAO_ONLY.md
git commit -m "Filter flights by aircraft ICAO code"
git push origin development
```
