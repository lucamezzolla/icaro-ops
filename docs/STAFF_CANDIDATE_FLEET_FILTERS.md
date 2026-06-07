# Staff candidate fleet filters

This patch changes the Staff hiring dialog so the candidate table starts empty and is populated only after a manual search/filter action.

## Behavior

- The hiring table starts empty.
- The default role filter is `PILOT`.
- `Only ratings for my fleet` is enabled by default for pilot searches.
- The backend filters pilot candidates by the type ratings required by the aircraft owned by the current company.
- If the available candidate pool does not contain enough pilots for an owned aircraft type, the API generates additional fictional pilot candidates with:
  - `CPL`
  - `IR`
  - the required aircraft type rating
- The target candidate pool is at least two available qualified pilots per owned aircraft, because each operational aircraft requires two active qualified pilots.

## Files

- `src/js/staff-hiring-table-dialog.js`
- `api/public/staff/candidates.php`
- `src/css/staff.css` via `docs/patch_staff_candidate_fleet_filters.py`

## Checks

```bash
php -l api/public/staff/candidates.php
node --check src/js/staff-hiring-table-dialog.js
```
