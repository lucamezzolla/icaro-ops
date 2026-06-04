# Visible bases on dashboard and selectable side details

This patch fixes three dashboard map issues:

- `/` and `/index.html` now show visible bases even without `companyId`.
- Player and rival base icons now use the same marker size.
- Clicking a base marker updates the left operations panel with the selected base details, in addition to opening the popup.

## New endpoint

```text
api/public/map/bases.php
```

It returns limited public data for player company bases and virtual rival bases.

## Apply

```bash
cd /home/luca/Documenti/html/icaro-ops
unzip -o /home/luca/Scaricati/icaro-ops-map-visible-bases-selection-patch.zip
```

## Test

```bash
curl "http://127.0.0.1:8080/api/public/map/bases.php"
```

Then open:

```text
http://127.0.0.1:8080/
```

and:

```text
http://127.0.0.1:8080/index.html?companyId=1
```
