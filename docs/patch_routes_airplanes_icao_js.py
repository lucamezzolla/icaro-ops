#!/usr/bin/env python3
from pathlib import Path

path = Path("src/js/routes.js")
text = path.read_text(encoding="utf-8")

text = text.replace("Preferred models", "Airplanes")
text = text.replace("Preferred model", "Airplanes")

text = text.replace(
    "service.compatible_aircraft_model_codes ||",
    "service.compatible_aircraft_icao_codes || service.compatible_aircraft_model_codes ||"
)

text = text.replace(
    "s.compatible_aircraft_model_codes || s.model_code ||",
    "s.compatible_aircraft_icao_codes || s.compatible_aircraft_model_codes || s.icao_type_code || s.model_code ||"
)

# If the table helper was named modelCodesLabel, keep name but prefer ICAO code payload.
text = text.replace(
'''function modelCodesLabel(service) {
  return escapeHtml(
    service.compatible_aircraft_model_codes ||
    service.model_code ||
    "C208B_GRAND_CARAVAN_EX"
  );
}''',
'''function modelCodesLabel(service) {
  return escapeHtml(
    service.compatible_aircraft_icao_codes ||
    service.icao_type_code ||
    "C208"
  );
}'''
)

path.write_text(text, encoding="utf-8")
print("OK: routes.js now displays ICAO aircraft type codes in Airplanes.")
