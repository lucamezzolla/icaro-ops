# Maintenance technician availability and schedule impact

This patch improves maintenance scheduling.

## New behavior

When scheduling maintenance, the backend now checks:

```text
- aircraft belongs to logged company
- aircraft is on ground
- aircraft is not already in maintenance
- at least one active qualified technician exists
- technician is not already busy with another in-progress maintenance event
- maintenance duration does not overlap the next scheduled route for that aircraft
```

If maintenance overlaps a future route, API returns:

```json
{
  "error": "MAINTENANCE_OVERLAPS_NEXT_FLIGHT",
  "impact": {
    "delay_risk_minutes": 120,
    "estimated_penalty_amount": 1000.0
  }
}
```

To accept the risk anyway, post with:

```json
{
  "aircraft_id": 1,
  "force": true
}
```

Then the system creates:

```text
- aircraft_operational_events row
- mailbox warning
- assigned technician id
- estimated penalty/risk
```

## Apply

```bash
cd /home/luca/Documenti/html/icaro-ops
unzip -o /home/luca/Scaricati/icaro-ops-maintenance-technician-schedule-impact-patch.zip
sudo mysql icaro_ops < db/mysql/081_maintenance_technician_schedule_impact.sql
```

## Files

```text
db/mysql/081_maintenance_technician_schedule_impact.sql
api/public/maintenance/schedule.php
docs/MAINTENANCE_TECHNICIAN_SCHEDULE_IMPACT.md
```

## Design note

This does not yet automatically delay the future route. It creates the operational risk and mailbox warning. The dispatch engine will later consume these route/aircraft states and apply actual delay/cancel/substitution decisions.
