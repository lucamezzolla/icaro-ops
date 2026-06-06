# Services table cleanup and airplane model dialog

## Apply

```bash
cd /home/luca/Documenti/html/icaro-ops
unzip -o /home/luca/Scaricati/icaro-ops-services-airplanes-detail-remove-patch.zip

python3 docs/patch_routes_airplanes_dialog_remove.py
python3 docs/patch_routes_headers_scheduled_airplanes.py
cat docs/routes_airplanes_dialog_css_append.css >> src/css/routes.css
```

Refresh:

```text
Ctrl + F5
```

## Changes

Table columns become:

```text
Service / Air route
Route
Scheduled
Airplanes
Actions
```

`Scheduled` displays `HH:mm`, or `Not scheduled`.

`Airplanes` displays clickable ICAO aircraft type designators, for example:

```text
C208, PC12, DHC6, L410
```

Clicking a code opens a generic aircraft model card with image and technical data.

The ticket price is removed from the table and remains in service details.

Service details now include:

```text
Remove service
```
