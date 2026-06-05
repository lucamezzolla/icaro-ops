# Abstract crew cost economy

This patch makes route economics more abstract and more suitable for short routes.

## Apply

```bash
cd /home/luca/Documenti/html/icaro-ops
unzip -o /home/luca/Scaricati/icaro-ops-abstract-crew-cost-economy-patch.zip
sudo mysql icaro_ops < db/mysql/088_staff_hourly_rate_and_economy_rebalance.sql
python3 docs/patch_staff_cost_profile.py
python3 docs/patch_routes_preview_abstract_cost.py
```

## New interpretation

For pilots:

```text
salary_per_flight = leg fee
hourly_rate = hourly operating cost
daily_retainer = fixed company daily cost, not charged to each flight
revenue_share_percent = variable bonus on ticket revenue
```

For technicians:

```text
daily_retainer = daily technician cost
hourly_rate = maintenance work hourly cost
salary_per_flight = 0
```

## Route preview formula

```text
crew_cost =
  SUM(leg_fee + hourly_rate * block_hours + revenue_share)
```

The route preview now shows:

```text
low / expected / high revenue and profit
suggested ticket price
crew formula
crew base cost before revenue share
```

## Why

The previous model charged too much fixed crew cost on short routes, making flights like LIRA -> LIRZ unrealistic.
This model works better for short and long routes because it scales with block time.
