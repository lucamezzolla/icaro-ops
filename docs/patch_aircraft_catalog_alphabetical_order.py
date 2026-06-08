#!/usr/bin/env python3
from pathlib import Path
import re

root = Path.cwd()
catalog = root / "api/public/fleet/catalog.php"
fleet = root / "src/js/fleet.js"

catalog_text = catalog.read_text(encoding="utf-8")
# Replace the catalog FROM/ORDER section so inactive duplicate/generic rows are hidden
# and the initial catalog order is the aircraft display name.
pattern = re.compile(
    r"FROM aircraft_models\s*(?:WHERE\s+COALESCE\(is_active,\s*1\)\s*=\s*1\s*)?ORDER BY\s+.*?\n(?=\")",
    re.DOTALL,
)
replacement = """FROM aircraft_models
    WHERE COALESCE(is_active, 1) = 1
    ORDER BY
      manufacturer,
      model_name,
      icao_type_code,
      model_code
"""
new_catalog, count = pattern.subn(replacement, catalog_text, count=1)
if count != 1:
    raise SystemExit("Could not patch catalog.php ORDER BY / active filter safely")
catalog.write_text(new_catalog, encoding="utf-8")

fleet_text = fleet.read_text(encoding="utf-8")
fleet_text = fleet_text.replace(
    "catalogAircraft = sortAircraftByPurchasePrice(data.aircraft || []);",
    "catalogAircraft = sortAircraftByCatalogName(data.aircraft || []);",
)

if "function sortAircraftByCatalogName" not in fleet_text:
    insert = r'''
function aircraftCatalogDisplayName(row) {
  return `${row.manufacturer || ""} ${row.model_name || ""}`
    .replace(/\s+/g, " ")
    .trim();
}

function sortAircraftByCatalogName(rows) {
  return [...rows].sort((a, b) => {
    const nameDelta = aircraftCatalogDisplayName(a).localeCompare(
      aircraftCatalogDisplayName(b),
      undefined,
      { sensitivity: "base", numeric: true }
    );

    if (nameDelta !== 0) {
      return nameDelta;
    }

    return String(a.icao_type_code || a.model_code || "").localeCompare(
      String(b.icao_type_code || b.model_code || ""),
      undefined,
      { sensitivity: "base", numeric: true }
    );
  });
}

'''
    marker = "function aircraftPurchasePriceValue(row)"
    if marker not in fleet_text:
        raise SystemExit("Could not find insertion point for catalog name sorter")
    fleet_text = fleet_text.replace(marker, insert + marker, 1)

fleet.write_text(fleet_text, encoding="utf-8")
print("Patched aircraft catalog alphabetical order and active-only catalog loading.")
