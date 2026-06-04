# Map airport search and missing company endpoint

This patch adds:

- `api/public/company/current.php`
- `api/public/rivals/bases.php`
- `api/public/airports/search.php`
- map search UI in `index.html`
- search handling in `src/js/dashboard-map.js`

## Why

If `GET /api/public/company/current.php?companyId=1` returns 404, the endpoint file is missing locally.

This patch restores that endpoint and adds an airport search box. You can search:

```text
Ciampino
LIRA
Rome
Fiumicino
```

## Apply

```bash
cd /home/luca/Documenti/html/icaro-ops
unzip -o /home/luca/Scaricati/icaro-ops-map-airport-search-patch.zip
```

## Test API

```bash
curl "http://127.0.0.1:8080/api/public/airports/search.php?q=Ciampino"
```

```bash
curl "http://127.0.0.1:8080/api/public/company/current.php?companyId=1"
```
