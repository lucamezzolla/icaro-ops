# Flights filters and empty initial table

This patch changes the Flights view as requested.

## Changes

- Removes the intro sentence:

```text
Flights
Create on-demand or scheduled flights and open details for operational rules and generated flight instances.
```

- Adds filters above the flights table:
  - Departure
  - Arrival
  - Airplane
  - Scheduled

- The flights table is initially empty.
- The table is populated only after pressing **Apply filters**.
- **Clear** resets filters and returns the table to the empty initial state.

## Apply

From the project root:

```bash
unzip -o /home/luca/Scaricati/icaro-ops-flights-filters-empty-initial-patch.zip
python3 docs/patch_flights_filters_empty_initial.py

node --check src/js/routes.js
```

Then hard-refresh the Flights page.

## Rollback

```bash
git restore routes.html src/js/routes.js
rm -f docs/patch_flights_filters_empty_initial.py docs/FLIGHTS_FILTERS_EMPTY_INITIAL.md
```

## Commit

```bash
git add routes.html src/js/routes.js docs/patch_flights_filters_empty_initial.py docs/FLIGHTS_FILTERS_EMPTY_INITIAL.md
git commit -m "Add flights table filters"
git push origin development
```
