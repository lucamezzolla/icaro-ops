# Algeria airport import

This patch imports Algeria airports from the first country PDF list.

## Source interpretation

The PDF table contains:

- City served
- Province
- ICAO
- IATA
- Airport name
- Coordinates
- AIP/chart links
- Rating

The source groups airports by type:

- International airports
- National airports
- Military airports
- Other airports

## Imported rows

Only rows with an ICAO code are imported because `airports.icao_code` is the primary key.

Imported rows: 50

Rows without ICAO code are intentionally skipped for now.

## Added airport fields

The patch adds these fields to `airports`:

- `service_category`
- `aip_url`
- `chart_url`
- `source_rating_percent`

## Install

Copy the files into the project, then run:

```bash
cd /home/luca/Documenti/html/icaro-ops
sudo mysql icaro_ops < db/mysql/999_apply_algeria_patch.sql
```

## Verification

```sql
SELECT service_category, COUNT(*)
FROM airports
WHERE country_id = (
  SELECT id FROM countries WHERE name = 'Algeria' AND world_region_code = 'AFRICA'
)
GROUP BY service_category;
```

Expected approximate result:

```text
INTERNATIONAL  18
NATIONAL       15
MILITARY        7
OTHER          10
```
