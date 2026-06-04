# Signup backend

This patch adds the first real signup backend.

## Files

```text
api/config.example.php
api/lib/bootstrap.php
api/public/starting-base/regions.php
api/public/starting-base/countries.php
api/public/starting-base/airports.php
api/public/signup.php
db/mysql/063_create_signup_company_tables.sql
src/js/signup.js
```

## Requirements on Trisquel

```bash
sudo apt install php php-cli php-mysql
```

## Database setup

First make sure the normalized starting-base view exists:

```bash
sudo mysql icaro_ops < db/mysql/062_create_starting_base_selection_view.sql
```

Then create signup/company tables:

```bash
sudo mysql icaro_ops < db/mysql/063_create_signup_company_tables.sql
```

## DB user

For local development you can temporarily use an existing MySQL user.

Cleaner local option:

```sql
CREATE USER IF NOT EXISTS 'icaro_ops_app'@'localhost' IDENTIFIED BY 'change-me';
GRANT SELECT, INSERT, UPDATE ON icaro_ops.* TO 'icaro_ops_app'@'localhost';
FLUSH PRIVILEGES;
```

## Local config

```bash
cp api/config.example.php api/config.local.php
nano api/config.local.php
```

`api/config.local.php` must not be committed.

## Run locally

From project root:

```bash
php -S 127.0.0.1:8080
```

Then open:

```text
http://127.0.0.1:8080/signup.html
```

## What signup does

The signup endpoint:

1. validates nickname, company name, language, currency and starting airport
2. checks the selected airport exists in `v_starting_base_airports`
3. creates a row in `players`
4. creates a row in `companies`
5. sets `budget_amount = 0.00`
6. creates an offer generation state row, ready for the future local offer generator
