# Player identity, virtual rivals and airport capacity

This patch changes signup and dashboard behavior.

## Changes

- Signup asks for first name and last name instead of nickname.
- Base details show the company owner.
- `Base market` wording becomes `Local market potential`.
- Market values are potential scores, not actual passengers/cargo.
- Adds virtual rival companies separate from physical users.
- Adds airport base capacity profiles.
- Sets LIRA / Rome Ciampino as MEDIUM with max 2 total bases.
- Moves map search to the right.
- Makes Search button blue like the UTC/topbar background.

## Apply

```bash
cd /home/luca/Documenti/html/icaro-ops
unzip -o /home/luca/Scaricati/icaro-ops-player-rivals-capacity-ui-patch.zip
sudo mysql icaro_ops < db/mysql/065_player_identity_rivals_airport_capacity.sql
```

## Test

```bash
curl "http://127.0.0.1:8080/api/public/company/current.php?companyId=1"
```

Create a new company from:

```text
http://127.0.0.1:8080/signup.html
```

## Notes

Existing development test players may have null first/last name. New signups use first and last name.
