# Live aircraft profit panel

Adds the estimated financial result to the left Live aircraft panel.

The panel now shows:

- estimated profit/loss/break-even result
- passenger revenue
- total operating cost
- currency

The backend endpoint `api/public/flights/active-detail.php` already exposes `passenger_revenue`, `total_operating_cost`, `profit_amount`, and `currency_code`, so this patch only updates `src/js/map-aircraft-left-panel.js`.

## Apply

```bash
python3 docs/patch_live_aircraft_profit_panel.py
node --check src/js/map-aircraft-left-panel.js
```

Then reload the browser with Ctrl+F5.
