# Fleet remove detail Actions section and right-align Refresh

This patch keeps aircraft actions in the aircraft detail dialog footer and removes the redundant `Actions` section from the detail body.

It also aligns the Fleet table `Refresh` button to the right above the owned-aircraft table.

## Files touched

- `fleet.html`
- `src/js/fleet.js`
- `src/css/fleet.css`

## Verification

```bash
node --check src/js/fleet.js
```
