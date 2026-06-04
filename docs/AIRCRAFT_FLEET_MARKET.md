# Aircraft fleet and used-aircraft market

This patch introduces the first aircraft system for Icaro Ops.

## Tables

### `aircraft_models`

Catalog of aircraft types/models.

Examples:

- Cessna 208B Grand Caravan EX
- Pilatus PC-12 NGX
- Beechcraft King Air 360
- DHC-6 Twin Otter Series 400
- L 410 NG
- Saab 340B
- ATR 42-600
- Embraer EMB 120ER Brasilia
- Concorde as inactive/endgame placeholder

### `company_aircraft`

Concrete aircraft owned or leased by a company.

Example:

```text
registration_code = I-ABCD
aircraft_model_id = C208B Grand Caravan EX
company_id = 1
condition_percent = 92.50
status = AVAILABLE
```

### `aircraft_purchase_offers`

Used-aircraft purchase offers between companies.

The buyer can offer money for an aircraft owned by another company. The seller may accept or reject based on future game logic.

## Important gameplay logic

The used-aircraft evaluation engine should consider:

- offered price versus current market value
- aircraft condition
- aircraft age and airframe hours
- whether the seller has enough other aircraft
- whether the aircraft is needed for active routes
- seller financial health
- seller strategy
- buyer reputation
- future operational needs

## Apply

```bash
cd /home/luca/Documenti/html/icaro-ops
unzip -o /home/luca/Scaricati/icaro-ops-aircraft-fleet-market-patch.zip
sudo mysql icaro_ops < db/mysql/067_create_aircraft_fleet_market.sql
```

## Test

```bash
sudo mysql icaro_ops -e "
SELECT
  manufacturer,
  model_name,
  model_code,
  aircraft_category,
  operation_role,
  passenger_capacity_standard,
  range_km,
  required_runway_m,
  new_purchase_price,
  is_active,
  is_endgame
FROM aircraft_models
ORDER BY is_endgame, unlock_reputation_score, manufacturer, model_name;
"
```

## Notes

The initial aircraft values are sufficient for development and balancing, but they must be reviewed before public release. The catalog is intentionally small now; the final catalog should include all relevant commercial aircraft and helicopters.
