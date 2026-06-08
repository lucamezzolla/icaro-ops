# Icaro Ops database bootstrap

This patch introduces one factory-reset SQL file:

```text
db/mysql/000_bootstrap_icaro_ops.sql
```

The script recreates the `icaro_ops` database from scratch and loads the essential seed data needed to start or develop the game on a clean machine.

## What is included as seed data

- `air_routes`
- `aircraft_maintenance_profiles`
- `aircraft_models`
- `airlines`
- `airport_capacity_profiles`
- `airport_game_profiles`
- `airport_gameplay_profiles`
- `airport_icao_aliases`
- `airport_market_overrides`
- `airport_market_profiles`
- `airport_runway_source_notes`
- `airport_starting_base_blacklist`
- `airport_starting_base_overrides`
- `airports`
- `countries`
- `game_settings`
- `icao_prefixes`
- `reputation_rules`
- `staff_candidate_licenses`
- `staff_candidates`
- `staff_license_types`
- `world_regions`

This includes the cleaned aircraft catalog, airports with coordinates, countries, world regions, ICAO prefixes, airport gameplay/capacity/market profiles, reputation rules, maintenance profiles, staff candidates and license data.

## What is intentionally empty

The runtime/player tables are created but their data is not inserted:

- `aircraft_operational_events`
- `aircraft_purchase_offers`
- `airport_base_slot_offers`
- `companies`
- `company_aircraft`
- `company_financial_events`
- `company_mailbox_messages`
- `company_market_offer_generation_state`
- `company_routes`
- `company_staff`
- `company_staff_licenses`
- `dev_budget_overrides`
- `dev_unlimited_budget_accounts`
- `dev_unlimited_budget_companies`
- `flight_dispatch_requirements`
- `game_mailbox_messages`
- `players`
- `reputation_journal`
- `rival_companies`
- `rival_company_aircraft`
- `rival_company_bases`
- `route_dispatch_attempts`
- `scheduled_flight_instances`
- `scheduled_services`

This avoids carrying over Luca's local development game state, owned aircraft, current flights, company staff, rival state, mailbox, reputation journal, and dev budget override state.

## How to test on a temporary database

The bootstrap currently creates `icaro_ops`. To test without touching the real DB, create a temporary copy of the script with the database name replaced:

```bash
cd /home/luca/Documenti/html/icaro-ops

sed 's/`icaro_ops`/`icaro_ops_bootstrap_test`/g'   db/mysql/000_bootstrap_icaro_ops.sql   > /tmp/000_bootstrap_icaro_ops_test.sql

sudo mysql < /tmp/000_bootstrap_icaro_ops_test.sql
```

Then verify core data:

```bash
sudo mysql icaro_ops_bootstrap_test -e "
SELECT COUNT(*) AS aircraft_models FROM aircraft_models;
SELECT COUNT(*) AS active_aircraft_models FROM aircraft_models WHERE is_active = 1;
SELECT COUNT(*) AS airports FROM airports;
SELECT COUNT(*) AS countries FROM countries;
SELECT COUNT(*) AS world_regions FROM world_regions;
SELECT COUNT(*) AS runtime_companies_should_be_zero FROM companies;
SELECT COUNT(*) AS runtime_company_aircraft_should_be_zero FROM company_aircraft;
"
```

## How to apply as factory reset

Only after a successful test:

```bash
cd /home/luca/Documenti/html/icaro-ops
sudo mysql < db/mysql/000_bootstrap_icaro_ops.sql
```

## Cleaning old migrations

Do not delete old SQL migrations until the bootstrap has been tested. This patch includes a helper:

```bash
./tools/archive_legacy_mysql_migrations.sh
```

It moves old SQL files to `db/mysql/archive_legacy_migrations/` instead of deleting them immediately.
