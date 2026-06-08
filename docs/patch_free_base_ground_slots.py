#!/usr/bin/env python3
from pathlib import Path

PROJECT = Path.cwd()
DASHBOARD_JS = PROJECT / "src/js/dashboard-map.js"

HELPER = 'function freeGroundSlotsFromCapacity(capacity = {}, data = {}) {\n  const maxGround = firstDefined(\n    capacity.max_aircraft_on_ground,\n    data.max_aircraft_on_ground\n  );\n  const atBase = firstDefined(\n    capacity.aircraft_at_base_count,\n    data.aircraft_at_base_count\n  );\n\n  if (maxGround === undefined || atBase === undefined) {\n    return undefined;\n  }\n\n  const free = Number(maxGround) - Number(atBase);\n  return Number.isFinite(free) ? Math.max(0, free) : undefined;\n}\n\nfunction freeGroundSlotsFromBase(base = {}) {\n  if (base.free_ground_aircraft_slots !== undefined && base.free_ground_aircraft_slots !== null && base.free_ground_aircraft_slots !== "") {\n    return base.free_ground_aircraft_slots;\n  }\n\n  const maxGround = base.max_aircraft_on_ground;\n  const atBase = base.aircraft_at_base_count;\n\n  if (maxGround === undefined || maxGround === null || atBase === undefined || atBase === null) {\n    return undefined;\n  }\n\n  const free = Number(maxGround) - Number(atBase);\n  return Number.isFinite(free) ? Math.max(0, free) : undefined;\n}\n'

def read(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path}")
    return path.read_text(encoding="utf-8")

def write(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")

def insert_helper(js: str) -> str:
    if "function freeGroundSlotsFromCapacity(" in js:
        return js

    marker = "\nfunction firstDefined("
    if marker in js:
        return js.replace(marker, "\n" + HELPER.rstrip() + "\n" + marker, 1)

    marker = "\nfunction formatPair("
    if marker in js:
        return js.replace(marker, "\n" + HELPER.rstrip() + "\n" + marker, 1)

    return js.rstrip() + "\n\n" + HELPER.rstrip() + "\n"

def main() -> None:
    js = read(DASHBOARD_JS)
    original = js

    js = insert_helper(js)

    old_block = '''firstDefined(
      capacity.free_ground_aircraft_slots,
      data.free_ground_aircraft_slots
    )'''
    new_block = '''firstDefined(
      capacity.free_ground_aircraft_slots,
      data.free_ground_aircraft_slots,
      freeGroundSlotsFromCapacity(capacity, data)
    )'''
    js = js.replace(old_block, new_block)

    old_sidebar = '''setSidebarValue("Free base ground slots", base.free_ground_aircraft_slots);'''
    new_sidebar = '''setSidebarValue("Free base ground slots", freeGroundSlotsFromBase(base));'''
    js = js.replace(old_sidebar, new_sidebar)

    old_summary = '''${summaryRow("Free base ground slots", base.free_ground_aircraft_slots)}'''
    new_summary = '''${summaryRow("Free base ground slots", freeGroundSlotsFromBase(base))}'''
    js = js.replace(old_summary, new_summary)

    if js == original:
        raise RuntimeError("No changes were applied to src/js/dashboard-map.js")

    write(DASHBOARD_JS, js)
    print("Patched dashboard-map.js: Free base ground slots now falls back to max ground - aircraft at base.")

if __name__ == "__main__":
    main()
