# Base marker offset and initial map fit

This patch improves the operations map when multiple bases share the same airport.

## Changes

- If the player HQ and a virtual rival base share the same airport, their markers are slightly offset around the real airport coordinates.
- This allows clicking both icons independently.
- The map now fits to all visible base locations as soon as the dashboard loads.
- If there is only one base, it zooms to that base.
- If no base is available, it shows the world overview.

## Apply

```bash
cd /home/luca/Documenti/html/icaro-ops
unzip -o /home/luca/Scaricati/icaro-ops-base-marker-offset-fit-patch.zip
```

Then reload:

```text
http://127.0.0.1:8080/index.html?companyId=1
```

## Note

The offset is visual only. The real airport coordinates remain unchanged in the database.
