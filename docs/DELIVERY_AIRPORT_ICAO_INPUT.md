# Delivery airport ICAO input

This patch updates the Fleet aircraft purchase flow.

## Change

The delivery airport dialog is no longer an airport search UI.
It now asks only for the ICAO airport code where the new aircraft must be delivered.

The frontend performs only minimal input validation:

- uppercase letters only
- 4-letter ICAO code format

The real airport existence validation remains on the backend. If the game cannot find the submitted airport, the backend error is shown to the player.

## Expected flow

Fleet → Buy aircraft → Buy → enter ICAO code → Continue → confirm purchase.

After a successful purchase, the dialog closes, the Fleet view is shown again, and the owned aircraft table is reloaded.
