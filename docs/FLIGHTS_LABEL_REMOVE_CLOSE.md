# Flights label, remove behavior, conditional start and dialog close

## Apply

```bash
cd /home/luca/Documenti/html/icaro-ops
unzip -o /home/luca/Scaricati/icaro-ops-flights-label-remove-close-patch.zip

python3 docs/patch_routes_flights_label_remove_close.py
python3 docs/patch_routes_html_flights_label_close.py
```

Refresh:

```text
Ctrl + F5
```

## Changes

The view now uses `Flights` wording instead of `Services`.

The list endpoint hides cancelled rows:

```text
service_status <> CANCELLED
```

So after `Remove flight route`, the row disappears immediately after reload.

`Start flight now` appears only for:

```text
ON_DEMAND
```

Scheduled rows do not show that button.

Dialog X buttons are forced to close their parent dialog.
