#!/usr/bin/env python3
from pathlib import Path

path = Path('src/js/fleet.js')
text = path.read_text(encoding='utf-8')

old = '''  const rowEngine = row => normalize(row.engine_type || row.engineType);
  const rowIcao = row => normalize(row.icao_type_code || row.model_code || row.iata_type_code);
  const rowPax = row => numberOrNull(row.passenger_capacity_standard ?? row.passenger_capacity_max);
  const rowPrice = row => numberOrNull(row.new_purchase_price ?? row.base_purchase_price ?? aircraftPurchasePriceValue(row));
  const rowText = row => normalize([
    row.manufacturer,
    row.model_name,
    row.model_code,
    row.icao_type_code,
    row.iata_type_code,
    row.operation_role,
    row.engine_type
  ].filter(Boolean).join(" "));
'''
new = '''  const rowEngine = row => normalize(row.engine_type || row.engineType);
  const rowCodeText = row => normalize([
    row.icao_type_code,
    row.iata_type_code,
    row.model_code,
    row.aircraft_model_code,
    row.code
  ].filter(Boolean).join(" "));
  const rowPax = row => {
    const standard = numberOrNull(row.passenger_capacity_standard);
    const maximum = numberOrNull(row.passenger_capacity_max);

    if (standard === null) {
      return maximum;
    }

    if (maximum === null) {
      return standard;
    }

    return Math.max(standard, maximum);
  };
  const rowPrice = row => numberOrNull(row.new_purchase_price ?? row.base_purchase_price ?? aircraftPurchasePriceValue(row));
  const rowText = row => normalize([
    row.manufacturer,
    row.model_name,
    row.model_code,
    row.aircraft_model_code,
    row.icao_type_code,
    row.iata_type_code,
    row.operation_role,
    row.engine_type
  ].filter(Boolean).join(" "));
'''
if old not in text:
    raise SystemExit('Could not find row helper block in src/js/fleet.js')
text = text.replace(old, new, 1)

old = '''    if (icao && !rowIcao(row).includes(icao)) {
      return false;
    }
'''
new = '''    if (icao && !rowCodeText(row).includes(icao)) {
      return false;
    }
'''
if old not in text:
    raise SystemExit('Could not find ICAO filter condition in src/js/fleet.js')
text = text.replace(old, new, 1)

old = '''          <input id="aircraftMarketFilterIcao" type="text" placeholder="A320, B738, CONC" autocomplete="off">
'''
new = '''          <input id="aircraftMarketFilterIcao" type="text" placeholder="ICAO, IATA or model code" autocomplete="off">
'''
text = text.replace(old, new, 1)

path.write_text(text, encoding='utf-8')
print('Patched src/js/fleet.js: combined filters now match ICAO/IATA/model code and use max passenger capacity.')
