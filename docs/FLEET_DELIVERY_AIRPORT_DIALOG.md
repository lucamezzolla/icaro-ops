# Fleet delivery airport dialog

This patch updates the Fleet purchase flow.

## Problem

`api/public/fleet/buy-new.php` now requires `delivery_airport_icao_code`, but the Fleet page `Buy new aircraft` dialog was still posting only `aircraft_model_id`.

That caused this backend validation error:

```text
Select a valid delivery airport before buying this aircraft.
```

## Fix

The Fleet purchase flow now:

1. Opens a small delivery airport dialog before purchase.
2. Lets the player search airports by ICAO, IATA, city or airport name.
3. Posts both `aircraft_model_id` and `delivery_airport_icao_code` to `api/public/fleet/buy-new.php`.
4. Closes the market/detail dialogs after a successful purchase.
5. Reloads the Fleet table with `loadFleet()` and shows the success message on the Fleet view.

## Verification

```bash
node --check src/js/fleet.js
```

Then open Fleet, click **Buy aircraft**, choose an aircraft, click **Buy**, choose the delivery airport, confirm, and verify that the owned aircraft table is refreshed.
