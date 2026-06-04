# Private Fleet navigation and base budget display

This patch removes the need for visible `companyId` navigation.

## Changes

- Fleet should be opened as:

```text
fleet.html
```

not:

```text
fleet.html?companyId=1
```

- The active company is read from browser `sessionStorage`.
- If the dashboard is opened with `companyId` during development, it stores that company as the active session company.
- Base details now show budget for player companies and virtual rivals.
- Virtual rivals now have simulated `budget_amount` and `currency_code`.

## Apply

```bash
cd /home/luca/Documenti/html/icaro-ops
unzip -o /home/luca/Scaricati/icaro-ops-private-fleet-budget-patch.zip
sudo mysql icaro_ops < db/mysql/070_private_fleet_navigation_and_rival_budget.sql
```

## Important

During development, if Fleet says no active company was found, open the dashboard once with:

```text
http://127.0.0.1:8080/index.html?companyId=1
```

Then click Fleet. The URL should become:

```text
http://127.0.0.1:8080/fleet.html
```

In a real authenticated version, this session value will be replaced by server-side login/session ownership checks.
