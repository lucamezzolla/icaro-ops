# Airplanes column with ICAO aircraft type codes

This patch renames `Preferred models` to:

```text
Airplanes
```

and displays ICAO aircraft type designators such as:

```text
C208, PC12, DHC6, L410
```

instead of internal model codes such as:

```text
C208B_GRAND_CARAVAN_EX
```

## Apply

```bash
cd /home/luca/Documenti/html/icaro-ops
unzip -o /home/luca/Scaricati/icaro-ops-airplanes-icao-codes-patch.zip

sudo mysql icaro_ops < db/mysql/093_aircraft_icao_codes_and_airplanes_column.sql

python3 docs/patch_routes_airplanes_column.py
python3 docs/patch_routes_airplanes_icao_js.py
```

Refresh:

```text
Ctrl + F5
```

## Notes

Internally, `scheduled_services.compatible_aircraft_model_codes` can still store model codes for dispatch logic.

The API resolves those model codes to `aircraft_models.icao_type_code` and exposes:

```text
compatible_aircraft_icao_codes
```

The UI uses this field for the `Airplanes` column.
