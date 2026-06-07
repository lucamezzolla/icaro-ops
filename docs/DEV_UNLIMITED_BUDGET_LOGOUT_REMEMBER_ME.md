# Developer unlimited budget, logout and remember-me login

## Apply

```bash
cd /home/luca/Documenti/html/icaro-ops
unzip -o /home/luca/Scaricati/icaro-ops-dev-unlimited-budget-logout-remember-me-patch.zip

sudo mysql icaro_ops < db/mysql/104_dev_unlimited_budget_logout_remember_me.sql

python3 docs/patch_logout_button_and_remember_me_ui.py
python3 docs/patch_login_php_remember_session.py

php -l api/public/auth/logout.php
php -l api/lib/remember-login.php
php -l api/public/auth/login.php
```

Refresh:

```text
Ctrl + F5
```

## Developer unlimited budget

The account `lucamezzolla@gmail.com` is mapped into:

```text
dev_unlimited_budget_accounts
dev_unlimited_budget_companies
```

The company budget is kept at:

```text
999999999999.00
```

through a database trigger.

This is a development/testing rule, not a gameplay advantage.

## Logout

Adds:

```text
api/public/auth/logout.php
src/js/auth-session-ui.js
```

The UI patch adds a Logout button to HTML pages except login/register pages.

## Remember me

Adds:

```text
api/lib/remember-login.php
src/js/login-remember-me.js
```

The login form gets `Remember me on this browser`.

When checked, the login request receives:

```json
{"remember_me": true}
```

The login PHP patch tries to call:

```php
remember_login_if_requested($payload);
```

after successful authentication.

If login fails after patching, send:

```bash
sed -n '1,220p' api/public/auth/login.php
```
