# Development open aircraft market

## Apply

```bash
cd /home/luca/Documenti/html/icaro-ops
unzip -o /home/luca/Scaricati/icaro-ops-open-aircraft-market-dev-patch.zip

sudo mysql icaro_ops < db/mysql/099_dev_open_aircraft_market_budget.sql
python3 docs/patch_fleet_ui_budget_only_market.py
```

Then refresh:

```text
Ctrl + F5
```

## What changes

This replaces the previous temporary ATR-only test idea with a broader development mode.

### Budget

All companies get:

```text
500,000,000.00
```

This is intentionally huge for development testing.

### Fleet market

`Fleet -> Buy new aircraft` now shows every aircraft model in `aircraft_models`.

No more hidden C208-only catalog.

### Purchase rule

The only blocker is:

```text
company budget >= aircraft price
```

Removed purchase blockers:

```text
- pilot count
- type rating
- base level
- current company level
- reputation
- endgame lock
- is_available_new
- is_active
```

The aircraft is still bought as a real `company_aircraft` row and the price is still deducted from budget.

## Important

This is a development/testing mode, not final gameplay balancing.

Later we can reintroduce progression rules cleanly, probably behind a setting such as:

```text
market_mode = DEVELOPMENT_OPEN
market_mode = GAME_PROGRESSION
```
