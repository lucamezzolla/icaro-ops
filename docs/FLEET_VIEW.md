# Fleet view

This patch adds the first Fleet management page.

## Files

```text
fleet.html
src/css/fleet.css
src/js/fleet.js

api/public/fleet/my-aircraft.php
api/public/fleet/aircraft-models.php
api/public/fleet/buy-new.php
api/public/fleet/used-market.php
api/public/fleet/list-for-sale.php
api/public/fleet/purchase-offer.php

db/mysql/069_create_fleet_views.sql
```

## Features

The first Fleet page can:

- show the selected company
- show base aircraft capacity
- list owned/leased aircraft
- show the active aircraft catalog
- attempt new aircraft purchase
- list owned aircraft for sale
- show used aircraft market listings
- create used-aircraft purchase offers

## Apply

```bash
cd /home/luca/Documenti/html/icaro-ops
unzip -o /home/luca/Scaricati/icaro-ops-fleet-view-patch.zip
sudo mysql icaro_ops < db/mysql/069_create_fleet_views.sql
```

## Open

```text
http://127.0.0.1:8080/fleet.html?companyId=1
```

## Important

At the moment the company budget is probably `0.00`, so new aircraft purchase will correctly fail with insufficient funds. This is expected until the game introduces starter contracts, leasing or initial tutorial financing.

## Future work

- leasing flow
- aircraft maintenance UI
- accept/reject/counter-offer logic for used-aircraft offers
- rival virtual offer evaluation engine
- Fleet route assignment
- aircraft type-rating requirements for pilots
