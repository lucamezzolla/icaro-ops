#!/usr/bin/env python3
from pathlib import Path

targets = [
    Path("src/js/fleet-market-table-dialog.js"),
    Path("src/js/fleet.js"),
]

helper = '''
function aircraftPurchasePriceValue(row) {
  const candidates = [
    row.new_purchase_price,
    row.base_purchase_price,
    row.purchase_price,
    row.estimated_new_price,
    row.catalog_price,
    row.price_amount,
    row.new_cost_amount,
    row.price
  ];

  for (const value of candidates) {
    const number = Number(value);

    if (Number.isFinite(number) && number > 0) {
      return number;
    }
  }

  return Number.MAX_SAFE_INTEGER;
}

function sortAircraftByPurchasePrice(rows) {
  return [...rows].sort((a, b) => {
    const priceDelta = aircraftPurchasePriceValue(a) - aircraftPurchasePriceValue(b);

    if (priceDelta !== 0) {
      return priceDelta;
    }

    return String(a.icao_type_code || a.model_code || a.model_name || "")
      .localeCompare(String(b.icao_type_code || b.model_code || b.model_name || ""));
  });
}

'''

for path in targets:
    if not path.exists():
        print(f"SKIP: {path} not found")
        continue

    text = path.read_text(encoding="utf-8")
    original = text

    if "function sortAircraftByPurchasePrice(" not in text:
        marker = "function escapeHtml"
        if marker in text:
            text = text.replace(marker, helper + marker, 1)
        else:
            text = text + "\n" + helper

    replacements = [
        ("renderAircraftTable(body, aircraft);", "renderAircraftTable(body, sortAircraftByPurchasePrice(aircraft));"),
        ("renderAircraftTable(container, aircraft);", "renderAircraftTable(container, sortAircraftByPurchasePrice(aircraft));"),
        ("catalogAircraft = data.aircraft || [];", "catalogAircraft = sortAircraftByPurchasePrice(data.aircraft || []);"),
        ("renderAircraftCatalog(catalogAircraft);", "renderAircraftCatalog(sortAircraftByPurchasePrice(catalogAircraft));"),
        ("renderAircraftCatalog(data.aircraft || []);", "renderAircraftCatalog(sortAircraftByPurchasePrice(data.aircraft || []));"),
    ]

    for old, new in replacements:
        text = text.replace(old, new)

    if text != original:
        path.write_text(text, encoding="utf-8")
        print(f"OK: patched {path}")
    else:
        print(f"OK: no changes needed for {path}")
