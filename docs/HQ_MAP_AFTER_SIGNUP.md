# HQ map after signup

This patch removes the conceptual fake aircraft from the initial dashboard and shows the company HQ/base instead.

## Files

```text
index.html
src/css/dashboard.css
src/js/dashboard-map.js
api/public/company/current.php
api/public/rivals/bases.php
docs/HQ_MAP_AFTER_SIGNUP.md
```

## Behavior

After signup:

- the company has no aircraft yet
- the map shows the selected base as an HQ/building marker
- the HQ marker can be clicked to show base and local market details
- rival bases can be displayed with limited public info
- aircraft markers will be added later only when `company_aircraft` exists

## Temporary development auth

For now the dashboard reads `company_id` from `sessionStorage`, saved after signup, or from:

```text
index.html?companyId=1
```

This is only for development. Later it must be replaced by secure login/session handling.

## Required existing setup

The following must already exist:

```text
api/lib/bootstrap.php
api/config.local.php
players
companies
v_starting_base_airports
```

## Test

Run:

```bash
php -S 127.0.0.1:8080
```

Open:

```text
http://127.0.0.1:8080/signup.html
```

Create a company, then the app redirects to `index.html` and displays the HQ marker.

You can also test directly:

```text
http://127.0.0.1:8080/index.html?companyId=1
```

## Security reminder

Current company loading by query string is temporary. Before real deployment:

- implement login
- use secure PHP sessions
- regenerate session IDs after login
- use HttpOnly/SameSite cookies
- add CSRF protection for state-changing actions
- add rate limiting
- do not expose private rival data
