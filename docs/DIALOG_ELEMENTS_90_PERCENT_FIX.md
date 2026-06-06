# Dialog element 90% size fix

## Problem

The previous CSS widened the internal dialog content/card, but not always the real `<dialog>` element.

So dialogs like:

```text
#routeDialog
#staffHiringTableDialog
```

could still stay narrow.

## Apply

```bash
cd /home/luca/Documenti/html/icaro-ops
unzip -o /home/luca/Scaricati/icaro-ops-dialog-elements-90-percent-fix-patch.zip

python3 docs/patch_dialog_elements_90_percent.py
```

Then refresh:

```text
Ctrl + F5
```

## What it fixes

The actual `<dialog>` elements are forced to:

```text
width: 90vw
height: 90vh
```

including:

```text
#routeDialog
#routeDetailDialog
#staffHiringTableDialog
#aircraftMarketTableDialog
#aircraftModelDialog
#chooseAircraftDialog
```

The internal form/card fills the dialog and only the body scrolls.
