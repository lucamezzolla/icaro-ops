# Fleet market filter focus and Buy footer button

Fixes:

1. `Search` and `Max price` losing focus while typing.
2. Moves `Buy this aircraft` to the aircraft model detail footer with a money icon.

## Apply

```bash
cd /home/luca/Documenti/html/icaro-ops
unzip -o /home/luca/Scaricati/icaro-ops-fleet-focus-buy-footer-patch-v3.zip
python3 docs/patch_fleet_focus_buy_footer_v3.py
node --check src/js/fleet.js
```

Then hard-refresh the browser.

## Rollback

```bash
git restore src/js/fleet.js src/css/fleet.css
rm -f docs/patch_fleet_focus_buy_footer_v3.py docs/FLEET_FOCUS_BUY_FOOTER_V3.md
```

## Commit

```bash
git add src/js/fleet.js src/css/fleet.css docs/patch_fleet_focus_buy_footer_v3.py docs/FLEET_FOCUS_BUY_FOOTER_V3.md
git commit -m "Improve fleet market filters and buy footer"
git push origin development
```
