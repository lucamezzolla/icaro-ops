# Aircraft image feature

This patch adds local aircraft images and a Fleet image dialog.

## Images

Images are installed in:

```text
src/assets/aircraft/
```

The filenames match the DB aircraft model codes in snake/lowercase style:

```text
c208b_grand_caravan_ex.png
pc12_ngx.png
b350_king_air_360.png
dhc6_twin_otter_400.png
l410_ng.png
saab_340b.png
atr42_600.png
emb120er_brasilia.png
concorde.png
```

## Apply

```bash
cd /home/luca/Documenti/html/icaro-ops
unzip -o /home/luca/Scaricati/icaro-ops-aircraft-image-feature-patch.zip
sudo mysql icaro_ops < db/mysql/071_add_aircraft_image_assets.sql
```

Then add the extra CSS to Fleet. If `fleet.html` does not already load it, add this line after `src/css/fleet.css`:

```html
<link rel="stylesheet" href="src/css/fleet-image-dialog.css">
```

Or append it directly:

```bash
cat src/css/fleet-image-dialog.css >> src/css/fleet.css
```

## Test

Open:

```text
http://127.0.0.1:8080/fleet.html
```

Every aircraft card in the catalog should show a thumbnail and an `Image` button.
