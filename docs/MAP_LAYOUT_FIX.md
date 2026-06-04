# Map layout fix

This patch fixes the broken Leaflet map layout after the HQ dashboard patch.

## Changes

- forces the map container to full viewport height
- removes the bottom-right help notification
- adds repeated `map.invalidateSize()` calls after initialization
- uses `fitBounds()` for a proper world overview
- formats UTC as `yyyy-MM-dd HH:mm:ss UTC`

## Apply

```bash
cd /home/luca/Documenti/html/icaro-ops
unzip -o /home/luca/Scaricati/icaro-ops-map-layout-fix-patch.zip
```

Then reload:

```text
http://127.0.0.1:8080/index.html
```

or:

```text
http://127.0.0.1:8080/index.html?companyId=1
```
