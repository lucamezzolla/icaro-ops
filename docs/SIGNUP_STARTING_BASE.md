# Signup and starting base selection

This patch adds the first signup/onboarding page and a normalized DB view for starting-base selection.

## Files

```text
signup.html
src/css/signup.css
src/js/signup.js
db/mysql/062_create_starting_base_selection_view.sql
docs/SIGNUP_STARTING_BASE.md
```

## Database design

The DB script does **not** create one profile row for every airport.

It creates only normalized rule/override tables:

```text
airport_starting_base_blacklist
airport_starting_base_overrides
airport_market_overrides
```

Then it creates:

```text
v_starting_base_airports
```

The view calculates starting-base eligibility and market scores from existing airport data plus manual overrides.

## Apply DB script

```bash
cd /home/luca/Documenti/html/icaro-ops
sudo mysql icaro_ops < db/mysql/062_create_starting_base_selection_view.sql
```

## Useful SQL for future API endpoints

Regions:

```sql
SELECT DISTINCT world_region_code, world_region_name
FROM v_starting_base_airports
ORDER BY world_region_name;
```

Countries by region:

```sql
SELECT DISTINCT country_id, country_name
FROM v_starting_base_airports
WHERE world_region_code = ?
ORDER BY country_name;
```

Airports by country:

```sql
SELECT *
FROM v_starting_base_airports
WHERE country_id = ?
ORDER BY starting_base_score DESC, airport_name;
```

## Frontend API contract

The page currently expects these future endpoints:

```text
GET  /api/public/starting-base/regions
GET  /api/public/starting-base/countries?region=EUROPE
GET  /api/public/starting-base/airports?countryId=123
POST /api/public/signup
```

The UI is ready, but the backend endpoints still need to be implemented.

## User-facing meaning

The signup page informs the user that the initial base affects:

- local passenger demand
- cargo opportunities
- tourism/private transfer work
- competition
- airport fees
- starting difficulty
- available local offers
