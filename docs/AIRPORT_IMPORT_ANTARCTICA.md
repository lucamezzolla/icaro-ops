# Antarctica airport import batch

Source file: `List_of_airports_in_Antarctica(2).pdf`

The source table includes airports, airstrips, skiways, runways and heliports.

## Import rule

`airports.icao_code` remains the primary key.

- If the source row has a 4-character ICAO code, that code is used.
- If ICAO is missing but the source row has a clean 4-character `Other code`, that code is used.
- Rows without a usable 4-character primary code are documented but not inserted into `airports`.
- Runway/surface details are stored in `airport_runway_source_notes`.

## Imported rows

Total imported rows: 47

By airport type:

{'AIRFIELD': 39, 'AIRSTRIP': 2, 'AIRPORT': 5, 'HELIPORT': 1}

Expected total airport count if current DB is 1501:

```text
1501 + 47 = 1548
```

## Skipped rows

Skipped rows: 23

Skipped by reason:

{'missing_4_char_primary_code': 23}

Details:

- Byrd Surface Skiway / operator=United States / ICAO=- / IATA=- / other=- / location=Marie Byrd Land / reason=missing_4_char_primary_code
- Davis Sea Ice Skiway (serving Davis) / operator=Australia / ICAO=- / IATA=- / other=- / location=Princess Elizabeth Land / reason=missing_4_char_primary_code
- Dome Fuji Skiway / operator=Japan / ICAO=- / IATA=- / other=- / location=Queen Maud Land / reason=missing_4_char_primary_code
- Druzh­hnaya 4 Skiway / operator=Russia / ICAO=- / IATA=- / other=- / location=Princess Elizabeth Land / reason=missing_4_char_primary_code
- Kunlun Skiway / operator=China / ICAO=- / IATA=- / other=- / location=East Antarctica / reason=missing_4_char_primary_code
- Mawson Plateau Skiway / operator=Australia / ICAO=- / IATA=- / other=- / location=Mac. Robertson Land / reason=missing_4_char_primary_code
- Mawson Sea Ice Skiway / operator=Australia / ICAO=- / IATA=- / other=- / location=Mac. Robertson Land / reason=missing_4_char_primary_code
- Perseus Airstrip (serving Princess Elisabeth Antarctica) / operator=Belgium / ICAO=- / IATA=- / other=- / location=Queen Maud Land / reason=missing_4_char_primary_code
- Plog Island Skiway (serving Davis) / operator=Australia / ICAO=- / IATA=- / other=- / location=Plog Island / reason=missing_4_char_primary_code
- Progress Skiway / operator=Russia / ICAO=- / IATA=- / other=- / location=Larsemann Hills / reason=missing_4_char_primary_code
- S17 Skiway / operator=Japan / ICAO=- / IATA=- / other=- / location=Enderby Land / reason=missing_4_char_primary_code
- Siple Dome Skiway / operator=United States / ICAO=- / IATA=- / other=- / location=Marie Byrd Land / reason=missing_4_char_primary_code
- Taishan Skiway / operator=China / ICAO=- / IATA=- / other=- / location=Princess Elizabeth Land / reason=missing_4_char_primary_code
- Arctowski Heliport / operator=Poland / ICAO=- / IATA=- / other=AG11177 / location=King George Island / reason=missing_4_char_primary_code
- Bharati Heliport / operator=India / ICAO=- / IATA=- / other=- / location=Larsemann Hills / reason=missing_4_char_primary_code
- Ferraz Heliport / operator=Brazil / ICAO=- / IATA=- / other=AG11178 / location=King George Island / reason=missing_4_char_primary_code
- Machu Picchu Heliport / operator=Peru / ICAO=- / IATA=- / other=AG11179 / location=King George Island / reason=missing_4_char_primary_code
- Maitri Helipad / operator=India / ICAO=- / IATA=- / other=- / location=Schirmacher Oasis / reason=missing_4_char_primary_code
- Marble Point Heliport Refuelling station / operator=United States / ICAO=- / IATA=- / other=GC0079 / location=Victoria Land / reason=missing_4_char_primary_code
- Primavera Heliport / operator=Argentina / ICAO=- / IATA=- / other=- / location=Cierva Cove / reason=missing_4_char_primary_code
- St. Kliment Ohridski Heliport / operator=Bulgaria / ICAO=- / IATA=- / other=- / location=Livingston Island / reason=missing_4_char_primary_code
- Artigas Heliport / operator=Uruguay / ICAO=- / IATA=- / other=- / location=King George Island / reason=missing_4_char_primary_code
- Zhongshan Station Heliport / operator=China / ICAO=- / IATA=- / other=- / location=Larsemann Hills / reason=missing_4_char_primary_code

## Apply

```bash
cd /home/luca/Documenti/html/icaro-ops
sudo mysql icaro_ops < db/mysql/999_apply_antarctica_airports_patch.sql
```

## Verification

```sql
SELECT
  c.name AS country_name,
  COUNT(*) AS total_airports
FROM airports a
JOIN countries c ON c.id = a.country_id
WHERE c.world_region_code = 'ANTARCTICA'
GROUP BY c.name;
```

If the diagnostic reports missing `Antarctica`, create or fix the country row in `countries` before re-running the patch.
