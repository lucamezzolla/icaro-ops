# Aircraft detail images patch v2

This patch fixes missing/broken aircraft images in the detail sheet.

## Why this exists

Some images are numbered, for example:

```text
src/assets/aircraft/290_socata_tbm_700.png
```

but the first aircraft images were generated as legacy non-numbered files, for example:

```text
src/assets/aircraft/c208b_grand_caravan_ex.png
src/assets/aircraft/airbus_a220_100.png
src/assets/aircraft/concorde.png
```

The previous resolver only searched the numbered prefix first. This v2 resolver also searches legacy filenames using DB fields like `model_code`, `manufacturer`, `model_name`, and `icao_type_code`.

## Apply

From the project root:

```bash
unzip -o icaro-ops-aircraft-detail-images-patch-v2.zip
```

Then reload the browser page.
