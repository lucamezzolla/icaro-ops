# West Africa 3 airport import batch

This patch imports airports for:

- Nigeria
- Senegal
- Sierra Leone
- Togo

The uploaded Saint Helena, Ascension and Tristan da Cunha document is not imported in this batch because it does not provide an airport table with ICAO/IATA fields. It mentions Saint Helena Airport and RAF Ascension Island, but importing those should be handled with a dedicated airport source.

## Compact model

No new fields were added to `airports`.

This patch uses a temporary table and `JOIN countries` / `JOIN icao_prefixes`.

## Imported rows

{'Nigeria': 41, 'Senegal': 19, 'Sierra Leone': 8, 'Togo': 7}

Total imported rows: 75

Expected total airport count if current DB is 1426:

```text
1426 + 75 = 1501
```

## Coordinates

Only Senegal has coordinates in the provided airport table.

Rows with coordinates:

{'Senegal': 19}

## Closed / former airports

{'Senegal': 2}

## Skipped rows without valid ICAO

{'Nigeria': 9, 'Senegal': 3}

Details:

- Nigeria: Lafia / Lafia Cargo Airport (missing_or_invalid_icao)
- Nigeria: Yenagoa / Bayelsa International Airport (missing_or_invalid_icao)
- Nigeria: Damaturu / Damaturu Cargo Airport (missing_or_invalid_icao)
- Nigeria: Azare / Azare Airstrip (missing_or_invalid_icao)
- Nigeria: Bacita / Bacita Airstrip (missing_or_invalid_icao)
- Nigeria: Bebi / Bebi Airstrip (missing_or_invalid_icao)
- Nigeria: Nguru / Nguru Airstrip (missing_or_invalid_icao)
- Nigeria: Potiskum / Potiskum Airstrip (missing_or_invalid_icao)
- Nigeria: Tuga / Tuga Airstrip (missing_or_invalid_icao)
- Senegal: Bignona / Bignona Airport (missing_or_invalid_icao)
- Senegal: Dakar / Ouakam Airfield (missing_or_invalid_icao)
- Senegal: Rufisque / Eknes Airfield (missing_or_invalid_icao)

## Skipped duplicate ICAO rows inside this batch

{'Nigeria': 3}

Details:

- Nigeria: Calabar / DNCA / Margaret Ekpo International Airport (duplicate_icao_in_source_batch)
- Nigeria: Uyo / DNAI / Victor Attah International Airport (duplicate_icao_in_source_batch)
- Nigeria: Makurdi / DNMK / Makurdi Air Force Base (duplicate_icao_in_source_batch)

## Apply

```bash
cd /home/luca/Documenti/html/icaro-ops
sudo mysql icaro_ops < db/mysql/999_apply_west_africa_3_airports_patch.sql
```
