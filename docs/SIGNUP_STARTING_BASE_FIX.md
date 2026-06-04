# Signup starting base selector fix

This patch restores the signup Starting base cascade:

```text
Region -> Country -> Airport
```

It replaces the simplified `src/js/signup.js` introduced during the auth patch.

## Apply

```bash
cd /home/luca/Documenti/html/icaro-ops
unzip -o /home/luca/Scaricati/icaro-ops-signup-starting-base-fix-patch.zip
```

## Expected protected pages

Do **not** add `auth-guard.js` to `signup.html` or `login.html`.

Protected pages should be:

```text
index.html
fleet.html
```

Public pages should be:

```text
login.html
signup.html
```

## Test endpoints

Run these manually:

```bash
curl "http://127.0.0.1:8080/api/public/starting-base/regions.php"
```

Then replace `EUROPE` with one returned code:

```bash
curl "http://127.0.0.1:8080/api/public/starting-base/countries.php?worldRegionCode=EUROPE"
```

Then replace `123` with one returned country id:

```bash
curl "http://127.0.0.1:8080/api/public/starting-base/airports.php?countryId=123"
```

## Test page

```text
http://127.0.0.1:8080/signup.html
```

The combo sequence should now populate again.
