# Add airplane and add staff table dialogs

## Apply

```bash
cd /home/luca/Documenti/html/icaro-ops
unzip -o /home/luca/Scaricati/icaro-ops-market-staff-table-dialogs-patch.zip

sudo mysql icaro_ops < db/mysql/100_world_staff_candidates_and_test_budget.sql
python3 docs/patch_include_market_staff_dialog_scripts.py
cat docs/table_dialogs_css_append.css >> src/css/fleet.css
cat docs/table_dialogs_css_append.css >> src/css/staff.css
```

Refresh:

```text
Ctrl + F5
```

## Add airplane

`Add airplane` / `Buy new aircraft` opens a dialog with a compact table:

```text
ICAO
Aircraft
Passengers
Range
Price
Actions
```

Each row has:

```text
Details
Buy
```

Details opens a generic aircraft model card.

## Add staff

`Add staff` opens a dialog with a compact table:

```text
Name
Role
Region
Experience
Licenses
Actions
```

Each row has:

```text
Details
Hire
```

## Staff candidates

The SQL creates worldwide staff candidate names, not only Italian names.

It adds:

```text
- pilot candidates
- technician candidates
- CPL + IR for pilots
- type-rating-like licenses generated from all aircraft_models
- A_AND_P + GENERAL_MAINT for technicians
```

This gives you candidates for many aircraft types in the DB and technicians for testing.
