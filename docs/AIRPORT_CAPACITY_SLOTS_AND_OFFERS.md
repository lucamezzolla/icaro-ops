# Airport capacity, base slots and slot offers

This patch applies a capacity rule to every airport and adds support for slot offers.

## Concepts

Every airport gets:

```text
airport_size_tier
max_player_bases
max_rival_bases
max_total_bases
```

Occupied bases are calculated from:

```text
companies
rival_company_bases
```

The capacity status is exposed by:

```text
v_airport_base_capacity_status
```

## LIRA / Rome Ciampino

Ciampino is manually reviewed as:

```text
airport_size_tier = MEDIUM
max_player_bases = 1
max_rival_bases = 1
max_total_bases = 2
```

So if the player and one virtual rival are both based there, LIRA is full.

## Slot offers

When an airport is full, a company may create a pending slot offer:

```text
airport_base_slot_offers
```

This does not automatically grant the slot yet. Later the game engine can decide whether to:

- accept
- reject
- expire
- counter-offer
- require higher airport fees
- force a rival to leave/sell a slot

## Apply

```bash
cd /home/luca/Documenti/html/icaro-ops
unzip -o /home/luca/Scaricati/icaro-ops-airport-capacity-slots-patch.zip
sudo mysql icaro_ops < db/mysql/066_airport_capacity_slots_and_offers.sql
```

## Test

```bash
sudo mysql icaro_ops -e "
SELECT *
FROM v_airport_base_capacity_status
WHERE airport_icao_code = 'LIRA';
"
```

```bash
curl "http://127.0.0.1:8080/api/public/airports/capacity.php?icao=LIRA"
```

Create a slot offer:

```bash
curl -i -X POST "http://127.0.0.1:8080/api/public/slot-offer.php" \
  -H "Content-Type: application/json" \
  -d '{
    "airport_icao_code": "LIRA",
    "requester_company_id": 1,
    "offered_amount": 25000,
    "currency_code": "EUR"
  }'
```
