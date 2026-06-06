# Scheduled departure hard fix

## Apply

```bash
cd /home/luca/Documenti/html/icaro-ops
unzip -o /home/luca/Scaricati/icaro-ops-scheduled-time-hard-fix-patch.zip

python3 docs/patch_scheduled_time_hard_fix.py
python3 docs/patch_scheduled_time_input_type.py
```

Refresh:

```text
Ctrl + F5
```

## What it fixes

When `Service type` is changed to:

```text
Scheduled
```

the field:

```text
Scheduled departure UTC
```

is forced to:

```text
enabled
required
10:00 if empty
```

When changed back to:

```text
On demand / non-scheduled
```

the field is:

```text
empty
disabled
not required
```
