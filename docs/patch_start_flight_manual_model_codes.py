#!/usr/bin/env python3
from pathlib import Path

path = Path("api/public/flights/start-service-now.php")
text = path.read_text(encoding="utf-8")

# Ensure service fetch selects compatible model codes.
if "ss.compatible_aircraft_model_codes" not in text:
    text = text.replace(
        "ss.preferred_aircraft_model_id, ss.required_aircraft_class,",
        "ss.preferred_aircraft_model_id, ss.required_aircraft_class, ss.compatible_aircraft_model_codes,"
    )

# Pass selected model codes to dispatch and do not block by theoretical range at start.
text = text.replace(
'''        'required_aircraft_class' => $service['required_aircraft_class'] ?: 'LIGHT_COMMERCIAL',
        'preferred_aircraft_model_id' => $service['preferred_aircraft_model_id'],
        'min_range_km' => $service['planned_distance_km'] ?? 0,
        'min_passenger_capacity' => 1,
        'max_passenger_capacity' => 19,''',
'''        'required_aircraft_class' => $service['required_aircraft_class'] ?: 'MANUAL_SELECTION',
        'preferred_aircraft_model_id' => $service['preferred_aircraft_model_id'],
        'allowed_model_codes' => $service['compatible_aircraft_model_codes'] ?? '',
        'min_range_km' => 0,
        'min_passenger_capacity' => 1,
        'max_passenger_capacity' => null,'''
)

path.write_text(text, encoding="utf-8")
print("OK: start-service-now.php dispatches only among manually selected models.")
