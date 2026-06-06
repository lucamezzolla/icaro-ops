# Flight code and duplicate-create fix

## What changed

The UI now has no user-facing route concept.

A created flight definition gets a public code:

```text
DOM-0001
INT-0001
CHT-0001
HEL-0001
CGO-0001
MIL-0001
RES-0001
TRN-0001
POS-0001
```

This value is stored in the legacy column:

```text
scheduled_services.flight_route_code
```

The internal unique `service_code` now includes an epoch:

```text
DOM-0008-C002-OND-ONDEMAND-1780758422
```

so recreating the same removed flight no longer fails with:

```text
Duplicate entry ... for key uq_scheduled_services_code
```

Removed/cancelled flights do not free their public code number.

## Apply

```bash
cd /home/luca/Documenti/html/icaro-ops
unzip -o /home/luca/Scaricati/icaro-ops-flight-code-duplicate-fix-patch.zip

python3 docs/patch_flight_code_display.py
```

Then refresh:

```text
Ctrl + F5
```
