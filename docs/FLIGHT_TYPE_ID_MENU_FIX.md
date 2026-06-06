# Flight type select ID and menu label fix

## Cause

In the uploaded project, `routes.html` has:

```html
<select id="flightType" name="flight_type">
```

but `src/js/routes.js` was listening to:

```js
document.querySelector("#serviceType")
```

So when you selected `Scheduled`, the JavaScript never received the change and the `Scheduled departure UTC` field stayed disabled.

## Apply

```bash
cd /home/luca/Documenti/html/icaro-ops
unzip -o /home/luca/Scaricati/icaro-ops-flight-type-id-menu-fix-patch.zip

python3 docs/patch_routes_flight_type_id.py
python3 docs/patch_routes_js_flight_type_selector.py
python3 docs/patch_all_menu_routes_to_flights_again.py
```

Then refresh:

```text
Ctrl + F5
```

## Result

- The menu label becomes `Flights`.
- The create dialog label becomes `Flight type`.
- Selecting `Scheduled` enables `Scheduled departure UTC`.
- Selecting `On demand / non-scheduled` disables and clears the time field.
