# Staff single effective status

This patch fixes the Staff table so the Status column shows one clear status only.

## Behavior

```text
ACTIVE + AVAILABLE        => AVAILABLE
ACTIVE + IN_FLIGHT        => IN FLIGHT / BUSY
DISMISSED / other status  => original employment status
```

So the UI no longer shows two badges like:

```text
ACTIVE  AVAILABLE
```

It shows only:

```text
AVAILABLE
```

or:

```text
IN FLIGHT / BUSY
```

## Apply

From the project root:

```bash
unzip -o /home/luca/Scaricati/icaro-ops-staff-single-status-patch.zip
python3 docs/patch_staff_single_status.py

node --check src/js/staff.js
```

Then hard-refresh Staff.

## Rollback

```bash
git restore src/js/staff.js
rm -f docs/patch_staff_single_status.py docs/STAFF_SINGLE_STATUS.md
```

## Commit

```bash
git add src/js/staff.js docs/patch_staff_single_status.py docs/STAFF_SINGLE_STATUS.md
git commit -m "Show single staff availability status"
git push origin development
```
