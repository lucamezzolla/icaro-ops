# Icaro Ops - aircraft image dialog and catalog image fix

This patch does two things:

1. In Fleet, when you open a purchased aircraft detail, the aircraft image becomes clickable.
   Clicking it opens the larger image dialog.

2. In the aircraft purchase/catalog detail, active aircraft models should resolve their images correctly.
   The catalog is also restricted to active aircraft models, so inactive/unprepared models such as ICP Savannah
   should not appear as purchasable/proposed entries with "No image available".

## Apply

From the project root:

```bash
unzip -o icaro-ops-aircraft-image-dialog-catalog-fix-patch.zip
python3 docs/patch_aircraft_image_dialog_catalog_fix.py
```

Then hard-refresh the browser page.

## Verify

Check PHP syntax:

```bash
php -l api/lib/aircraft-images.php
php -l api/public/fleet/catalog.php
php -l api/public/fleet/detail.php
php -l api/public/fleet/model-detail.php
php -l api/public/fleet/my-aircraft.php
```

Check whether Savannah is inactive:

```bash
sudo mysql icaro_ops -e "SELECT id, manufacturer, model_name, is_active FROM aircraft_models WHERE model_name LIKE '%Savannah%';"
```

If a model is inactive, it should no longer be shown by the aircraft purchase catalog API.
