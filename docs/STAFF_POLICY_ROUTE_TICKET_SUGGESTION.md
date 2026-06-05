# Staff policy and route ticket suggestion

## Staff

The hiring dialog now explains:

```text
2 active qualified pilots are required for each operational aircraft.
Recommended maintenance coverage: 1 qualified technician every 3 aircraft.
Candidate costs are indicative estimates.
```

Candidate costs are displayed as estimates, not definitive contract values.

Examples:

```text
est. 65 EUR/leg + 97 EUR/h + 1% revenue
est. 140 EUR/day + 55 EUR/h maintenance
```

## Routes

The Add Route ticket field starts at:

```text
0.00
```

When origin and destination are filled, the UI silently calls the economic preview and fills the suggested ticket price. The value remains editable.

## Apply

```bash
cd /home/luca/Documenti/html/icaro-ops
unzip -o /home/luca/Scaricati/icaro-ops-staff-policy-route-ticket-suggestion-patch.zip

python3 docs/patch_staff_policy_indicative_costs.py
python3 docs/patch_routes_ticket_suggestion.py
python3 docs/patch_routes_ticket_field.py
cat docs/staff_policy_route_ticket_css_append.css >> src/css/staff.css
cat docs/staff_policy_route_ticket_css_append.css >> src/css/routes.css
```

Refresh:

```text
Ctrl + F5
```
