# Pilots required per aircraft, technicians moved to maintenance

This patch applies the intended gameplay rule:

```text
Every aircraft requires 2 active qualified pilots.
Technicians are not flight crew and are not required to buy an aircraft or dispatch a normal flight.
Technicians are managed by maintenance/repair workflows.
```

## Apply

```bash
cd /home/luca/Documenti/html/icaro-ops
unzip -o /home/luca/Scaricati/icaro-ops-pilots-required-no-tech-dispatch-patch.zip
sudo mysql icaro_ops < db/mysql/079_pilots_required_no_technician_dispatch.sql
```

## What changes

### Buying aircraft

`api/public/fleet/buy-new.php` now checks pilot capacity:

```text
required pilots after purchase = (current aircraft + 1) * 2
```

For Cessna 208B it requires pilots with:

```text
CPL
C208_TYPE
```

### Route planning

`api/public/routes/create.php` no longer requires a technician.

It still requires two qualified pilots for the route.

### Dispatch

`api/public/flights/start-scheduled.php` no longer checks for technician.

It checks:

```text
- 2 assigned active qualified pilots
- available aircraft at origin
- aircraft not in maintenance / condition not too low
```

### Maintenance

Technicians remain important, but for:

```text
- planned maintenance
- repairs
- faults
- aircraft recovery
```

not as onboard crew.
