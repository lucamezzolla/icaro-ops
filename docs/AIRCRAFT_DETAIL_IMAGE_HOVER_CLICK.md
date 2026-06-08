# Owned aircraft detail image hover + click preview

This patch is intentionally small.

It changes only the owned aircraft detail image behavior:

- the image stays small in the detail sheet;
- on hover/focus it grows slightly as a visual hint;
- on click it opens the existing larger image dialog.

## Apply

From the project root:

```bash
unzip -o /home/luca/Scaricati/icaro-ops-aircraft-detail-image-hover-click-patch.zip
python3 docs/patch_aircraft_detail_image_hover_click.py
node --check src/js/fleet.js
```

Then hard-refresh the browser page.

## Rollback if needed

```bash
git restore src/js/fleet.js src/css/fleet.css
rm -f docs/patch_aircraft_detail_image_hover_click.py docs/AIRCRAFT_DETAIL_IMAGE_HOVER_CLICK.md
```

## Commit

```bash
git add src/js/fleet.js src/css/fleet.css docs/patch_aircraft_detail_image_hover_click.py docs/AIRCRAFT_DETAIL_IMAGE_HOVER_CLICK.md
git commit -m "Add aircraft detail image preview interaction"
git push origin development
```
