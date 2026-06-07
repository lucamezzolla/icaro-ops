# Update LPPT coordinates

Adds or updates Lisbon Humberto Delgado Airport (`LPPT`, IATA `LIS`) with coordinates usable by the map and flight systems.

Coordinates used:

```text
latitude:  38.7813000
longitude: -9.1359200
```

Run:

```bash
sudo mysql icaro_ops < db/mysql/116_update_lppt_coordinates.sql
```

Verify:

```bash
sudo mysql icaro_ops -e "
SELECT icao_code, iata_code, name, city, latitude, longitude, service_category, data_quality
FROM airports
WHERE icao_code = 'LPPT';
"
```

Expected result: one row for `LPPT` with non-null latitude and longitude.
