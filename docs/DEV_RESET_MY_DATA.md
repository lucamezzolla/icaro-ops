# Development reset current account

This patch adds a local-only development reset endpoint and a small web page.

## Files

```text
api/public/dev/reset-my-data.php
dev-reset.html
docs/DEV_RESET_MY_DATA.md
```

## Apply

```bash
cd /home/luca/Documenti/html/icaro-ops
unzip -o /home/luca/Scaricati/icaro-ops-dev-reset-my-data-patch.zip
```

No SQL is required.

## Open

```text
http://127.0.0.1:8080/dev-reset.html
```

You must be logged in.

Type:

```text
RESET_MY_ICARO_OPS_DATA
```

Then click reset.

## What it deletes

For the currently logged-in player/company:

```text
route_dispatch_attempts
reputation_journal
aircraft_operational_events
game_mailbox_messages
scheduled_flight_instances
company_routes
company_staff_licenses
company_staff
staff_candidates
aircraft_purchase_offers
company_aircraft
company_market_offer_generation_state
companies
players
```

Then it destroys the PHP session.

## Safety

The endpoint only accepts local requests from:

```text
127.0.0.1
::1
localhost
```

It also requires this JSON confirmation:

```json
{
  "confirm": "RESET_MY_ICARO_OPS_DATA"
}
```

## Curl test

```bash
curl -i -X POST "http://127.0.0.1:8080/api/public/dev/reset-my-data.php" \
  -H "Content-Type: application/json" \
  -d '{"confirm":"RESET_MY_ICARO_OPS_DATA"}'
```

The curl test works only if the request includes a valid logged-in PHP session cookie, so the web page is easier.
