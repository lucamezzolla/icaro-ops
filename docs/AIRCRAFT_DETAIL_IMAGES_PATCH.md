# Aircraft detail images patch

This patch connects aircraft model images placed in:

```text
src/assets/aircraft/
```

to the aircraft detail dialogs in the game.

## What it does

- Adds `api/lib/aircraft-images.php`.
- Normalizes `image_asset_path` values already stored in `aircraft_models`.
- If `image_asset_path` is empty, automatically resolves the image from the filename prefix:

```text
src/assets/aircraft/001_*.png
src/assets/aircraft/041_*.png
src/assets/aircraft/290_*.png
```

- Applies the resolver to:
  - owned fleet list
  - owned aircraft detail
  - aircraft market catalog
  - aircraft model detail
- Shows the aircraft image inside the owned aircraft detail sheet when available.
- Keeps the existing Image button, but now avoids opening an empty image dialog if an image is missing.

## How to apply

From the project root:

```bash
unzip -o icaro-ops-aircraft-detail-images-patch.zip
```

Then reload the app.

## Optional database backfill

The patch works even if `aircraft_models.image_asset_path` is empty, because the backend resolves files by ID prefix.

If you also want to persist image paths into the DB, run:

```bash
mysql -u icaro_ops_user -p icaro_ops < db/mysql/patch_aircraft_model_image_asset_paths.sql
```

The SQL file only updates `image_asset_path`; it does not modify prices, names, status, or gameplay data.
