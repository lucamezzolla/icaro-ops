#!/usr/bin/env python3
from pathlib import Path

path = Path("api/lib/dispatch-aircraft.php")
text = path.read_text(encoding="utf-8")

if "$allowedModelCodes" not in text:
    text = text.replace(
'''    $maxPassengerCapacity = isset($requirements['max_passenger_capacity']) ? (int)$requirements['max_passenger_capacity'] : null;''',
'''    $maxPassengerCapacity = isset($requirements['max_passenger_capacity']) ? (int)$requirements['max_passenger_capacity'] : null;
    $allowedModelCodes = $requirements['allowed_model_codes'] ?? [];

    if (is_string($allowedModelCodes)) {
        $allowedModelCodes = array_values(array_filter(array_map('trim', explode(',', $allowedModelCodes))));
    }

    if (!is_array($allowedModelCodes)) {
        $allowedModelCodes = [];
    }'''
    )

if "allowed_model_" not in text:
    text = text.replace(
'''    if ($maxPassengerCapacity !== null) {
        $sql .= " AND am.passenger_capacity_standard <= :max_passenger_capacity";
        $params['max_passenger_capacity'] = $maxPassengerCapacity;
    }

    $sql .= compatible_aircraft_class_sql($requiredClass);''',
'''    if ($maxPassengerCapacity !== null) {
        $sql .= " AND am.passenger_capacity_standard <= :max_passenger_capacity";
        $params['max_passenger_capacity'] = $maxPassengerCapacity;
    }

    if ($allowedModelCodes) {
        $modelPlaceholders = [];

        foreach (array_values($allowedModelCodes) as $index => $modelCode) {
            $paramName = "allowed_model_" . $index;
            $modelPlaceholders[] = ":" . $paramName;
            $params[$paramName] = $modelCode;
        }

        $sql .= " AND am.model_code IN (" . implode(",", $modelPlaceholders) . ")";
    } else {
        $sql .= compatible_aircraft_class_sql($requiredClass);
    }'''
    )

path.write_text(text, encoding="utf-8")
print("OK: dispatch-aircraft.php supports allowed_model_codes.")
