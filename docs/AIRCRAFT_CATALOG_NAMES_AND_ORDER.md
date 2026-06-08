# Aircraft catalog names, deduplication and alphabetical order

This patch cleans the aircraft catalog for the Buy new aircraft dialog.

## Database migration

`db/mysql/121_clean_aircraft_catalog_names_and_deduplicate.sql`

It updates `aircraft_models.manufacturer` and `aircraft_models.model_name` so the catalog displays professional aircraft names such as:

- `ICON Aircraft A5` instead of `Icon Icon A5`
- `Extra Aircraft EA-300 / EA-330 / EA-350` instead of `EXTRA EXTRA 300, 330, 350`
- `McDonnell Douglas MD-82` instead of misspelled or duplicated names

It also disables obvious non-purchasable generic or duplicate rows by setting `is_active = 0`, including the imported duplicate Concorde row. The curated Concorde row remains active.

## Code patch

`docs/patch_aircraft_catalog_alphabetical_order.py`

It updates the catalog endpoint and Fleet frontend so the initial Buy new aircraft catalog order is alphabetical by displayed aircraft name. The endpoint also excludes inactive catalog rows.
