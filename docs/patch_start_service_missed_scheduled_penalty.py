#!/usr/bin/env python3
from pathlib import Path

path = Path("api/public/flights/start-service-now.php")
text = path.read_text(encoding="utf-8")

# Add penalty require.
if "missed-scheduled-flight-penalty.php" not in text:
    text = text.replace(
        "require_once __DIR__ . '/../../lib/flight-dispatch-selection.php';",
        "require_once __DIR__ . '/../../lib/flight-dispatch-selection.php';\nrequire_once __DIR__ . '/../../lib/missed-scheduled-flight-penalty.php';"
    )

old = """    if (!$aircraft) {
        $pdo->rollBack();
        json_response([
            'error' => 'NO_AVAILABLE_AIRCRAFT_AT_ORIGIN',
            'message' => 'No compatible available aircraft is present at the flight origin airport.',
            'origin_airport_icao_code' => $service['origin_airport_icao_code'],
            'compatible_aircraft_model_codes' => $service['compatible_aircraft_model_codes'] ?? '',
        ], 409);
    }"""

new = """    if (!$aircraft) {
        if (!$isOnDemand) {
            apply_missed_scheduled_flight_penalty(
                $pdo,
                $companyId,
                $service,
                'No compatible available aircraft was present at the scheduled flight origin airport.'
            );

            $pdo->commit();

            json_response([
                'status' => 'SCHEDULED_FLIGHT_MISSED',
                'error' => 'NO_AVAILABLE_AIRCRAFT_AT_ORIGIN',
                'message' => 'Scheduled flight could not depart. A mailbox notification was sent, a temporary penalty was applied, and reputation was reduced.',
                'origin_airport_icao_code' => $service['origin_airport_icao_code'],
                'compatible_aircraft_model_codes' => $service['compatible_aircraft_model_codes'] ?? '',
                'penalty_amount' => '100000.00',
                'reputation_loss' => 10,
            ], 409);
        }

        $pdo->rollBack();
        json_response([
            'error' => 'NO_AVAILABLE_AIRCRAFT_AT_ORIGIN',
            'message' => 'No compatible available aircraft is present at the flight origin airport.',
            'origin_airport_icao_code' => $service['origin_airport_icao_code'],
            'compatible_aircraft_model_codes' => $service['compatible_aircraft_model_codes'] ?? '',
        ], 409);
    }"""

if old not in text:
    raise SystemExit("Could not find aircraft-not-found block in api/public/flights/start-service-now.php")

text = text.replace(old, new)

path.write_text(text, encoding="utf-8")
print("OK: scheduled no-aircraft path now applies mailbox, fine and reputation penalty.")
