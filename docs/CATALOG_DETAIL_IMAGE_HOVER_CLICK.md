# Catalog aircraft detail image hover/click fix

This patch completes the image preview interaction.

It does two things:

1. Applies the same hover/click behavior to aircraft model details opened from the aircraft market / sale dialog.
2. Removes the hover color/brightness/shadow effect, leaving only a slight scale-up.

## Apply

From the project root:

```bash
unzip -o /home/luca/Scaricati/icaro-ops-catalog-detail-image-hover-click-patch.zip
python3 docs/patch_catalog_detail_image_hover_click.py
node --check src/js/fleet.js
```

Then hard-refresh the browser page.

## Rollback if needed

```bash
git restore src/js/fleet.js src/css/fleet.css
rm -f docs/patch_catalog_detail_image_hover_click.py docs/CATALOG_DETAIL_IMAGE_HOVER_CLICK.md
```

## Commit

```bash
git add src/js/fleet.js src/css/fleet.css docs/patch_catalog_detail_image_hover_click.py docs/CATALOG_DETAIL_IMAGE_HOVER_CLICK.md
git commit -m "Add catalog aircraft image preview interaction"
git push origin development
```
