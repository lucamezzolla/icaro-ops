# Update airport coordinates from OurAirports

This patch generates a local MySQL migration that updates latitude and longitude
for airports already present in the Icaro Ops database.

Source dataset: OurAirports `airports.csv`.

Important rules:

- Existing airports are updated by ICAO code.
- The script does not insert thousands of new airports.
- Existing `VERIFIED` quality is preserved.
- Non-verified rows updated by this script are marked as `PARTIAL`.
- Existing `elevation_ft` values are preserved; missing elevation is filled when available.

Last generated summary:

- Matched existing airports: 8712
- Existing airports not found in OurAirports by ICAO/gps code: 629

Recommended commands:

```bash
python3 tools/update_airport_coordinates_from_ourairports.py
sudo mysql icaro_ops < db/mysql/117_update_airport_coordinates_from_ourairports.sql
```

Verification:

```bash
sudo mysql icaro_ops -e "
SELECT COUNT(*) AS airports_without_coordinates_remaining
FROM airports
WHERE latitude IS NULL OR longitude IS NULL;
"
```
