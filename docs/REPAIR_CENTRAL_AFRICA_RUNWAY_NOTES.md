# Repair Central Africa runway notes

The original v10 patch can fail in `039_seed_airport_runway_source_notes_central_africa.sql`
with a foreign key error.

This repair script inserts runway notes only for ICAO codes that already exist in `airports`.

## Apply

```bash
cd /home/luca/Documenti/html/icaro-ops
sudo mysql icaro_ops < db/mysql/041_repair_central_africa_runway_notes.sql
```

The script prints:

- missing runway-note ICAO codes, if any
- total airport count
- airport count for Angola, Cameroon, Chad and Central African Republic
