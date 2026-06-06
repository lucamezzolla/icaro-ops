# Routes table scheduled/on-demand and compatible models

## Apply

```bash
cd /home/luca/Documenti/html/icaro-ops
unzip -o /home/luca/Scaricati/icaro-ops-routes-scheduled-ondemand-models-patch.zip

sudo mysql icaro_ops < db/mysql/092_scheduled_ondemand_services.sql

python3 docs/patch_routes_scheduled_ondemand_ui.py
python3 docs/patch_routes_scheduled_ondemand_html.py
```

Refresh:

```text
Ctrl + F5
```

## Changes

Routes/Services table now shows:

```text
Service / Air route
Route
Scheduled
Preferred models
Ticket
Actions
```

It no longer shows:

```text
Required class
Status
```

## Creation

When creating a service, choose:

```text
Scheduled
On demand / non-scheduled
```

Scheduled requires departure time.

On demand has no fixed departure time and will later be used for extra/manual flights.

## Preferred models

For early-game LIGHT_COMMERCIAL routes the compatible list is:

```text
C208B_GRAND_CARAVAN_EX
PC12_NGX
DHC6_TWIN_OTTER_400
L410_NG
```
