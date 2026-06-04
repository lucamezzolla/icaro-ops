# Auth, initial budget and dev reset

## Apply

```bash
cd /home/luca/Documenti/html/icaro-ops
unzip -o /home/luca/Scaricati/icaro-ops-auth-budget-patch.zip
sudo mysql icaro_ops < db/mysql/072_auth_initial_budget.sql
```

## Optional development reset

This removes players, companies and company aircraft, but keeps airports and aircraft models.

```bash
sudo mysql icaro_ops < db/mysql/dev/901_reset_dev_players_companies.sql
```

## Login

Open:

```text
http://127.0.0.1:8080/login.html
```

## Signup

The updated `signup.php` now expects:

```json
{
  "first_name": "Mario",
  "last_name": "Rossi",
  "email": "mario@example.com",
  "password": "at-least-8-chars",
  "company_name": "Regional Test Air",
  "interface_language": "it",
  "currency_code": "EUR",
  "base_airport_icao_code": "LIRA"
}
```

New companies start with:

```text
7,000,000.00
```

from `game_settings.initial_company_budget`.

## Important

This is development-grade auth. Good foundations are included:

- `password_hash()`
- `password_verify()`
- PHP session
- HttpOnly cookie
- SameSite=Lax

Later production work should add:

- CSRF protection
- server-side authorization checks on every company endpoint
- rate limiting
- HTTPS secure cookies
- remember-me persistent tokens
