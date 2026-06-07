# Live aircraft compact profit dialog

This patch changes the Live aircraft panel profit display from a verbose inline economic summary to a compact clickable profit/loss value.

## Behavior

The Live aircraft panel shows only one compact value:

```text
Profit: 12,340.00 EUR
```

or:

```text
Loss: -4,500.00 EUR
```

Clicking the value opens a dialog with the full economic detail:

- route
- passengers
- revenue
- operating cost
- final profit/loss

## Check

```bash
node --check src/js/map-aircraft-left-panel.js
```
