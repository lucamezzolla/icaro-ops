#!/usr/bin/env python3
from pathlib import Path

ROOT = Path.cwd()
CATALOG = ROOT / "api/public/fleet/catalog.php"
DIALOG = ROOT / "src/js/fleet-market-table-dialog.js"
FILTERS = ROOT / "src/js/aircraft-market-filters.js"
DOC = ROOT / "docs/AIRCRAFT_MARKET_ENGINE_FILTER_FIX.md"


def fail(msg: str):
    raise SystemExit(msg)


def patch_catalog():
    path = CATALOG
    text = path.read_text()
    original = text

    # Ensure the API exposes engine/family values. The UI can then filter using real DB values.
    if "aircraft_family" not in text.split("FROM aircraft_models", 1)[0]:
        marker = "      operation_role,\n"
        if marker not in text:
            fail("catalog.php: could not find operation_role SELECT marker")
        text = text.replace(marker, marker + "      aircraft_family,\n      engine_type,\n", 1)
    elif "engine_type" not in text.split("FROM aircraft_models", 1)[0]:
        marker = "      aircraft_family,\n"
        if marker not in text:
            fail("catalog.php: could not find aircraft_family SELECT marker")
        text = text.replace(marker, marker + "      engine_type,\n", 1)

    if text != original:
        path.write_text(text)
        print(f"Patched {path}")
    else:
        print(f"No changes needed in {path}")


def patch_dialog():
    path = DIALOG
    text = path.read_text()
    original = text

    # Add data attributes to market rows. This avoids fragile text parsing and lets filters work
    # even when engine/family columns are not visible.
    if "data-aircraft-engine=" not in text:
        old = """            <tr>\n              <td><strong>${escapeHtml(row.icao_type_code || row.model_code)}</strong></td>"""
        new = """            <tr data-aircraft-icao="${escapeHtml(row.icao_type_code || row.model_code || "")}" data-aircraft-family="${escapeHtml(row.aircraft_family || "")}" data-aircraft-engine="${escapeHtml(row.engine_type || "")}" data-aircraft-price="${escapeHtml(row.new_purchase_price ?? "")}" data-aircraft-pax="${escapeHtml(row.passenger_capacity_standard ?? "")}">\n              <td><strong>${escapeHtml(row.icao_type_code || row.model_code)}</strong></td>"""
        if old not in text:
            # More tolerant replacement: first table row inside aircraft.map.
            old2 = """          ${aircraft.map(row => `\n            <tr>"""
            new2 = """          ${aircraft.map(row => `\n            <tr data-aircraft-icao="${escapeHtml(row.icao_type_code || row.model_code || "")}" data-aircraft-family="${escapeHtml(row.aircraft_family || "")}" data-aircraft-engine="${escapeHtml(row.engine_type || "")}" data-aircraft-price="${escapeHtml(row.new_purchase_price ?? "")}" data-aircraft-pax="${escapeHtml(row.passenger_capacity_standard ?? "")}">"""
            if old2 not in text:
                fail("fleet-market-table-dialog.js: could not find aircraft market row template")
            text = text.replace(old2, new2, 1)
        else:
            text = text.replace(old, new, 1)

    if text != original:
        path.write_text(text)
        print(f"Patched {path}")
    else:
        print(f"No changes needed in {path}")


def patch_filters():
    path = FILTERS
    text = path.read_text()
    original = text

    # Insert helper functions before extractAircraftRowData if missing.
    if "function normalizeEngineType" not in text:
        marker = "  function extractAircraftRowData(row) {\n"
        helpers = r'''  function normalizeEngineType(value) {
    const upper = String(value || "").trim().toUpperCase().replace(/[\s-]+/g, "_");

    if (!upper) {
      return "";
    }

    if (upper.includes("TURBOPROP")) {
      return "TURBOPROP";
    }

    if (upper.includes("TURBOSHAFT")) {
      return "TURBOSHAFT";
    }

    if (upper.includes("TURBOFAN") || upper.includes("TURBOJET") || upper === "JET" || upper.includes("_JET")) {
      return "JET";
    }

    if (upper.includes("PISTON")) {
      return "PISTON";
    }

    return upper;
  }

  function normalizeFamilyType(value) {
    const upper = String(value || "").trim().toUpperCase().replace(/[\s-]+/g, "_");

    if (!upper) {
      return "";
    }

    if (upper.includes("HELICOPTER") || upper.includes("ROTOR")) {
      return "HELICOPTER";
    }

    if (upper.includes("FIXED") || upper.includes("AIRPLANE") || upper.includes("AEROPLANE")) {
      return "FIXED_WING";
    }

    return upper;
  }

'''
        if marker not in text:
            fail("aircraft-market-filters.js: could not find extractAircraftRowData marker")
        text = text.replace(marker, helpers + marker, 1)

    old = '''  function extractAircraftRowData(row) {
    const text = normalize(row.textContent);
    const upper = text.toUpperCase();

    return {
      text,
      upper,
      icao: extractIcao(row, upper),
      price: extractPrice(upper),
      pax: extractPassengerCapacity(upper),
      family: extractOneOf(upper, ["FIXED_WING", "FIXED WING", "HELICOPTER"]),
      engine: extractOneOf(upper, ["PISTON", "TURBOPROP", "JET", "TURBOSHAFT"])
    };
  }
'''
    new = '''  function extractAircraftRowData(row) {
    const text = normalize(row.textContent);
    const upper = text.toUpperCase();
    const dataset = row.dataset || {};

    return {
      text,
      upper,
      icao: String(dataset.aircraftIcao || extractIcao(row, upper)).toUpperCase(),
      price: numberOrNull(String(dataset.aircraftPrice || "")) ?? extractPrice(upper),
      pax: numberOrNull(String(dataset.aircraftPax || "")) ?? extractPassengerCapacity(upper),
      family: normalizeFamilyType(dataset.aircraftFamily || extractOneOf(upper, ["FIXED_WING", "FIXED WING", "FIXED-WING", "HELICOPTER"])),
      engine: normalizeEngineType(dataset.aircraftEngine || extractOneOf(upper, ["TURBOFAN", "TURBOJET", "PISTON", "TURBOPROP", "JET", "TURBOSHAFT"]))
    };
  }
'''
    if old in text:
        text = text.replace(old, new, 1)
    elif "dataset.aircraftEngine" not in text:
        fail("aircraft-market-filters.js: extractAircraftRowData has an unexpected shape")

    old_engine_check = '''    if (criteria.engine && data.engine !== criteria.engine && !data.upper.includes(criteria.engine)) {
      return false;
    }
'''
    new_engine_check = '''    if (criteria.engine && data.engine !== criteria.engine) {
      return false;
    }
'''
    if old_engine_check in text:
        text = text.replace(old_engine_check, new_engine_check, 1)

    old_family_check = '''    if (criteria.family) {
      const normalizedFamily = data.family.replace(" ", "_");

      if (normalizedFamily !== criteria.family && !data.upper.includes(criteria.family)) {
        return false;
      }
    }
'''
    new_family_check = '''    if (criteria.family && data.family !== criteria.family) {
      return false;
    }
'''
    if old_family_check in text:
        text = text.replace(old_family_check, new_family_check, 1)

    if text != original:
        path.write_text(text)
        print(f"Patched {path}")
    else:
        print(f"No changes needed in {path}")


def write_doc():
    DOC.write_text("""# Aircraft market engine filter fix\n\nFixes the Buy new aircraft market filters so Engine = Jet uses the real `engine_type` value returned by the backend instead of trying to infer the engine from visible table text.\n\nChanges:\n\n- `api/public/fleet/catalog.php` now returns `aircraft_family` and `engine_type`.\n- `src/js/fleet-market-table-dialog.js` stores ICAO, family, engine, price and passenger capacity as `data-*` attributes on each aircraft row.\n- `src/js/aircraft-market-filters.js` reads those attributes and normalizes common engine values such as `TURBOFAN` and `TURBOJET` to `JET`.\n\nExpected result: selecting Engine = Jet should show jet aircraft such as Boeing 737 and Airbus A320 families when present in the catalog.\n""")
    print(f"Wrote {DOC}")


def main():
    for p in (CATALOG, DIALOG, FILTERS):
        if not p.exists():
            fail(f"Missing required file: {p}")
    patch_catalog()
    patch_dialog()
    patch_filters()
    write_doc()

if __name__ == "__main__":
    main()
