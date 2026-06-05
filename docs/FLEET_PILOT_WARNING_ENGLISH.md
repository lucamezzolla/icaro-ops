# Fleet pilot coverage warning in English

This patch simplifies the insufficient pilot coverage warning.

## Apply

```bash
cd /home/luca/Documenti/html/icaro-ops
unzip -o /home/luca/Scaricati/icaro-ops-fleet-pilot-warning-english-patch.zip
python3 docs/patch_fleet_pilot_warning_english.py
```

## Expected warning

```text
Pilot coverage is not sufficient for this purchase.
You need 2 more qualified pilots to buy this aircraft.
Required aircraft qualification: C208_TYPE
```

The number is calculated dynamically from:

```text
required_pilots_after_purchase - current_qualified_pilots
```
