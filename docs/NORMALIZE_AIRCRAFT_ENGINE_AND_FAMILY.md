# Normalize aircraft engine type and family

This patch adds migration:

```text
db/mysql/119_normalize_aircraft_engine_and_family.sql
```

## Goal

Normalize the values used by the aircraft market filters.

Before this migration, many rows had:

```text
aircraft_family = FIXED_WING
engine_type = JET
```

Those values are too generic for filtering.

## Rules used

### engine_type

`engine_type` is only the propulsion technology:

```text
PISTON
TURBOPROP
TURBOFAN
TURBOJET
TURBOSHAFT
```

UI filters should group them like this:

```text
Jet        -> TURBOFAN, TURBOJET
Turboprop  -> TURBOPROP
Piston     -> PISTON
Helicopter -> TURBOSHAFT
```

### aircraft_family

`aircraft_family` is the model/family group, for example:

```text
B737_FAMILY
A320_FAMILY
MD80_FAMILY
ATR_FAMILY
CONCORDE_FAMILY
```

## Concorde

Concorde should not use `SUPERSONIC` as `engine_type`.

Recommended values:

```text
engine_type = TURBOJET
aircraft_family = CONCORDE_FAMILY
```

Until a future `market_segment` column exists, this migration temporarily ensures:

```text
aircraft_category = SUPERSONIC
```

for Concorde rows only.

## Expected engine counts from the provided TSV

```text
TURBOFAN: 137
PISTON: 86
TURBOPROP: 60
TURBOSHAFT: 16
TURBOJET: 2
```

## Apply

```bash
cd /home/luca/Documenti/html/icaro-ops
sudo mysql icaro_ops < db/mysql/119_normalize_aircraft_engine_and_family.sql
```

## Verify

```bash
sudo mysql icaro_ops -e "
SELECT engine_type, COUNT(*) AS aircraft_count
FROM aircraft_models
GROUP BY engine_type
ORDER BY aircraft_count DESC;
"

sudo mysql icaro_ops -e "
SELECT id, manufacturer, model_name, icao_type_code, engine_type, aircraft_family, aircraft_category
FROM aircraft_models
WHERE aircraft_family IN ('B737_FAMILY','A320_FAMILY','CONCORDE_FAMILY','MD80_FAMILY')
ORDER BY aircraft_family, model_name;
"
```

## Browser test

After applying this migration and the aircraft market engine filter patch, reload with `Ctrl + F5`.

In **Fleet → + → Buy new aircraft**:

```text
Engine: Jet
```

must show A320/B737/other jet aircraft because the UI maps `Jet` to:

```text
TURBOFAN + TURBOJET
```
