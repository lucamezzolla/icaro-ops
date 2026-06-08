# Aircraft catalog cleanup: visibility, duplicates and professional names

This patch cleans the Buy new aircraft catalog without deleting aircraft model rows.

## Migration

`db/mysql/122_cleanup_aircraft_catalog_visibility_and_duplicates.sql`

The migration:

- hides non-commercial / non-airline aircraft by setting `is_active = 0`;
- hides obvious duplicate catalog rows;
- keeps the row with the most believable / curated data when duplicates exist;
- normalizes the names of affected rows;
- does not mass-update prices.

## Rows hidden from the purchase catalog

### Non-business / non-airline aircraft

These rows are kept in the database but hidden from the main purchase catalog:

- Extra EA-300 / EA-330 / EA-350 aerobatic series
- Aviat Pitts Special S-2S
- Bellanca Scout / Super Decathlon
- XtremeAir XA-42 Sbach 342
- ICON Aircraft A5
- Austflight Drifter
- Flight Design CTSL
- Diamond DV20 / DA20 Katana trainer-like rows
- Kitfox STi FreedomFox / Fox2
- Lancair Legacy
- Pipistrel Virus SW 121
- ICP Savannah
- JMB Aircraft VL-3
- Sting S4
- Tecnam P2002 Sierra
- Tecnam P2004 Bravo
- Tecnam P92
- Van's RV-14 / RV-14A
- Zlin Savage Cub / Shock Ultra
- Zenith STOL CH 801
- Waco vintage aircraft
- Schweizer 2-32 glider
- Hawker Hurricane Mk I
- P-51D Mustang
- Vought F4U Corsair
- De Havilland Mosquito
- SIAI-Marchetti SF-260
- Caproni Vizzola C-22J Ventura

### Duplicate / less believable rows

The migration keeps the more believable row visible:

- Concorde: keep id 9, hide id 285
- Cessna 208: keep id 1, hide ids 146 and 153
- DHC-6 Twin Otter: keep id 4, hide id 193
- Pilatus PC-12: keep id 2, hide id 256
- Saab 340: keep id 6, hide id 281
- Embraer EMB 120: keep id 8, hide id 207
- Beechcraft 1900: keep id 121, hide id 115
- Beechcraft King Air 350: keep id 118, hide id 123
- Dassault Falcon 50: keep id 186, hide id 188

## Frontend/API patch

`docs/patch_aircraft_catalog_active_alphabetical_order.py`

The patch updates `api/public/fleet/catalog.php` so the catalog:

- returns only `is_active = 1` rows;
- includes a `display_name` field;
- sorts alphabetically by `display_name`.

It also updates `src/js/fleet.js` so the Buy new aircraft table uses `display_name` and preserves the backend order.

## Price policy

This patch intentionally does not change prices in bulk. Current prices should still be treated as gameplay-estimated values unless individually verified.

A future migration should introduce a clearer price model, for example:

- `base_purchase_price`: gameplay price used for buying;
- `reference_real_price`: optional real-world reference estimate;
- `price_quality`: `GAMEPLAY_BALANCED`, `ESTIMATED`, `REALISTIC_RANGE`, `VERIFIED`.
