# Dispatch choice and wide dialogs

## Apply

```bash
cd /home/luca/Documenti/html/icaro-ops
unzip -o /home/luca/Scaricati/icaro-ops-flight-dispatch-choice-and-wide-dialogs-patch.zip

python3 docs/patch_routes_manual_dispatch_choice.py
cat docs/dialogs_90vw_90vh_css_append.css >> src/css/routes.css
cat docs/dialogs_90vw_90vh_css_append.css >> src/css/fleet.css
cat docs/dialogs_90vw_90vh_css_append.css >> src/css/staff.css
```

Refresh:

```text
Ctrl + F5
```

## Dialog size

All create/detail dialogs become 90vw x 90vh.

## Non-scheduled flights

Start flight now asks you to choose a compatible available aircraft at the origin airport.

If none are available, the flight cannot depart.

## Scheduled flights

The backend supports automatic aircraft selection for scheduled dispatch. It chooses among compatible available aircraft at the origin, sorted by estimated profit score.
