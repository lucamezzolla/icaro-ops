# Reputation rules

This patch adds configurable reputation automation.

## Apply

```bash
cd /home/luca/Documenti/html/icaro-ops
unzip -o /home/luca/Scaricati/icaro-ops-reputation-rules-patch.zip
sudo mysql icaro_ops < db/mysql/084_reputation_rules.sql
python3 docs/patch_reputation_completion.py
```

## Rules

Reputation deltas are stored in DB:

```sql
SELECT event_code, reputation_delta, description
FROM reputation_rules
ORDER BY event_code;
```

Initial values:

```text
FLIGHT_COMPLETED_PROFITABLE             +1
FLIGHT_COMPLETED_BREAK_EVEN_OR_LOSS      0
DISPATCH_CANCELLED_NO_AIRCRAFT          -8
DISPATCH_BLOCKED_CREW                   -4
DISPATCH_BLOCKED_MAINTENANCE            -6
MAINTENANCE_DELAY_ACCEPTED              -1
```

To rebalance later:

```sql
UPDATE reputation_rules
SET reputation_delta = 2
WHERE event_code = 'FLIGHT_COMPLETED_PROFITABLE';
```

## Notes

The included patch script wires successful flight completion into reputation:

```text
profit > 0  => +1 reputation
profit <= 0 =>  0 reputation
```

The dispatch engine can later be tightened to use the same helper for all negative events.
