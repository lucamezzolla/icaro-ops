#!/usr/bin/env python3
from pathlib import Path

catalog_path = Path('api/public/fleet/catalog.php')
text = catalog_path.read_text(encoding='utf-8')
original = text

# Add a display name computed by the backend. This avoids duplicated names such as
# "Icon Icon A5" when model_name already contains the manufacturer.
if 'AS display_name' not in text:
    marker = "      model_name,\n"
    replacement = """      model_name,
      CASE
        WHEN UPPER(TRIM(COALESCE(model_name, ''))) LIKE CONCAT(UPPER(TRIM(COALESCE(manufacturer, ''))), '%')
          THEN TRIM(COALESCE(model_name, ''))
        ELSE TRIM(CONCAT(TRIM(COALESCE(manufacturer, '')), ' ', TRIM(COALESCE(model_name, ''))))
      END AS display_name,
"""
    if marker not in text:
        raise SystemExit('Could not find model_name select marker in api/public/fleet/catalog.php')
    text = text.replace(marker, replacement, 1)

# Hide inactive catalog rows from Buy new aircraft.
if 'WHERE COALESCE(is_active, 1) = 1' not in text:
    marker = "    FROM aircraft_models\n"
    replacement = "    FROM aircraft_models\n    WHERE COALESCE(is_active, 1) = 1\n"
    if marker not in text:
        raise SystemExit('Could not find FROM aircraft_models marker in api/public/fleet/catalog.php')
    text = text.replace(marker, replacement, 1)

# Order the purchase catalog alphabetically by displayed aircraft name.
start = text.find('    ORDER BY\n')
if start == -1:
    raise SystemExit('Could not find ORDER BY block in api/public/fleet/catalog.php')
end = text.find('\n";', start)
if end == -1:
    raise SystemExit('Could not find end of SQL string after ORDER BY block')
order_block = """    ORDER BY
      display_name,
      icao_type_code,
      model_code
"""
text = text[:start] + order_block + text[end:]

if text != original:
    catalog_path.write_text(text, encoding='utf-8')
    print('Patched api/public/fleet/catalog.php for active-only alphabetical catalog order.')
else:
    print('api/public/fleet/catalog.php already patched.')

fleet_path = Path('src/js/fleet.js')
if fleet_path.exists():
    text = fleet_path.read_text(encoding='utf-8')
    original = text

    # Use backend display_name where available in the Buy new aircraft catalog.
    text = text.replace(
        '<td><strong>${escapeHtml(a.manufacturer)} ${escapeHtml(a.model_name)}</strong></td>',
        '<td><strong>${escapeHtml(a.display_name || `${a.manufacturer || ""} ${a.model_name || ""}`.trim() || "Aircraft")}</strong></td>'
    )

    # If the current local version has the newer filter rendering, patch any simple aircraft name expression too.
    text = text.replace(
        '${escapeHtml(a.manufacturer || "")} ${escapeHtml(a.model_name || "")}',
        '${escapeHtml(a.display_name || `${a.manufacturer || ""} ${a.model_name || ""}`.trim() || "Aircraft")}'
    )

    # Remove old price sorting on catalog load if this exact line exists.
    text = text.replace(
        'catalogAircraft = sortAircraftByPurchasePrice(data.aircraft || []);',
        'catalogAircraft = data.aircraft || [];'
    )

    if text != original:
        fleet_path.write_text(text, encoding='utf-8')
        print('Patched src/js/fleet.js to use display_name and preserve backend alphabetical order.')
    else:
        print('src/js/fleet.js did not need display_name/order changes.')
