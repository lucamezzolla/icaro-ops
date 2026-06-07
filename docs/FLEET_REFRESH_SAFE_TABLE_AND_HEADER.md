# Fleet refresh safe table and header cleanup

This patch removes the redundant `Owned aircraft` header/description from the Fleet card and fixes the `Budget only` cleanup script so it only touches the Buy aircraft dialog.

The previous runtime cleanup script scanned every table in the page. During refreshes it could remove columns from the owned Fleet table, making the header and table layout progressively inconsistent.

Changes:

- Remove the redundant Fleet card title and description.
- Keep the Fleet table header stable on Refresh.
- Keep `Last position` as the aircraft location column header.
- Show `In flight` for flying aircraft in the Fleet table.
- Remove the `Budget only` catalog column physically when possible.
- Scope the fallback cleanup script to `#buyAircraftDialog` only.
