# Missed scheduled flight penalty

## Apply

```bash
cd /home/luca/Documenti/html/icaro-ops
unzip -o /home/luca/Scaricati/icaro-ops-scheduled-missed-flight-penalty-patch.zip

sudo mysql icaro_ops < db/mysql/101_mailbox_and_scheduled_missed_penalty.sql
python3 docs/patch_start_service_missed_scheduled_penalty.py
```

## Rule

For scheduled flights only:

```text
If no compatible available aircraft is found at the origin airport:
- send mailbox message
- apply temporary fine: 100,000 in company currency
- reputation -10
```

For non-scheduled flights:

```text
No automatic fine.
The UI simply tells the player that the flight cannot depart.
```

## Temporary values to rebalance later

```text
Fine: 100,000
Reputation loss: 10
```

These are temporary. Later we should replace them with a proper damage/disruption model:

```text
passenger compensation
route importance
delay/cancellation history
company size
airport disruption
reputation sensitivity
```
