# Staff candidate coverage

This patch improves the hiring market.

## What changes

When `api/public/staff/candidates.php` is opened, the game ensures that the candidate pool contains enough useful applicants:

```text
- at least 6 C208-qualified pilots
- more C208-qualified pilots if pilot coverage is insufficient
- at least 3 C208 maintenance technicians
- more C208 maintenance technicians if technician coverage is insufficient
```

## Rules

Pilots:

```text
2 active C208-qualified pilots are required for each operational aircraft.
```

Technicians:

```text
recommended: 1 C208-qualified technician every 3 aircraft
```

Technician shortage does **not** block aircraft purchase. It will later affect maintenance time, delays and reliability.

## Files

```text
api/public/staff/candidates.php
api/public/staff/hire.php
docs/STAFF_CANDIDATE_COVERAGE.md
```

## Apply

```bash
cd /home/luca/Documenti/html/icaro-ops
unzip -o /home/luca/Scaricati/icaro-ops-staff-candidate-coverage-patch.zip
```

Then open:

```text
http://127.0.0.1:8080/staff.html
```

Click `Add staff`.

## Quick test

From a logged-in browser:

```text
http://127.0.0.1:8080/api/public/staff/candidates.php
```

You should see a JSON response with `coverage` and `candidates`.
