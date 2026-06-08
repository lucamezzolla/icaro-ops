#!/usr/bin/env python3
from pathlib import Path

PROJECT = Path.cwd()

DISPATCHER_LIB = PROJECT / "api/lib/scheduled-service-dispatcher.php"
PROCESS_DUE = PROJECT / "api/public/dispatch/process-due-routes.php"
ACTIVE_FLIGHTS = PROJECT / "api/public/flights/active.php"
FLIGHT_LAYER = PROJECT / "src/js/flight-layer.js"

DISPATCHER_LIB_CONTENT = '<?php\ndeclare(strict_types=1);\n\nrequire_once __DIR__ . \'/flight-completion.php\';\nrequire_once __DIR__ . \'/flight-dispatch-selection.php\';\nrequire_once __DIR__ . \'/missed-scheduled-flight-penalty.php\';\n\nconst ICARO_AUTO_DISPATCH_STATUS = \'AUTO_DISPATCHED_SCHEDULED\';\n\n/**\n * Process scheduled services that are due in UTC.\n *\n * Important:\n * - This function never starts future flights early.\n * - $windowMinutes is a look-back window for overdue services.\n * - Manual "start now" flights do not consume the daily automatic schedule.\n */\nfunction process_due_scheduled_services(\n    PDO $pdo,\n    int $companyId,\n    int $windowMinutes = 240,\n    bool $devForce = false\n): array {\n    $windowMinutes = max(1, min(1440, $windowMinutes));\n\n    complete_due_flights($pdo, $companyId);\n\n    $services = icaro_fetch_due_scheduled_services($pdo, $companyId, $windowMinutes, $devForce);\n    $results = [];\n\n    foreach ($services as $serviceRow) {\n        $serviceId = (int)$serviceRow[\'service_id\'];\n        $scheduledDeparture = (string)$serviceRow[\'scheduled_departure_at_utc\'];\n        $flightDateUtc = substr($scheduledDeparture, 0, 10);\n\n        if (icaro_already_auto_processed_service_date($pdo, $companyId, $serviceId, $flightDateUtc)) {\n            $results[] = [\n                \'service_id\' => $serviceId,\n                \'result\' => \'SKIPPED_ALREADY_AUTO_PROCESSED\',\n                \'scheduled_departure_at_utc\' => $scheduledDeparture,\n            ];\n            continue;\n        }\n\n        $service = dispatch_fetch_flight_definition_for_update($pdo, $companyId, $serviceId);\n\n        if (!$service) {\n            $results[] = [\n                \'service_id\' => $serviceId,\n                \'result\' => \'SKIPPED_SERVICE_NOT_FOUND\',\n            ];\n            continue;\n        }\n\n        /*\n         * The route-aware row has all fields needed by the automatic dispatcher.\n         * Merge it with the existing shared dispatcher definition so older helpers\n         * remain compatible.\n         */\n        $service = array_merge($serviceRow, $service);\n\n        $aircraft = dispatch_choose_best_available_aircraft($pdo, $companyId, $service);\n\n        if (!$aircraft) {\n            apply_missed_scheduled_flight_penalty(\n                $pdo,\n                $companyId,\n                $service,\n                \'No compatible available aircraft was present at the scheduled flight origin airport.\'\n            );\n\n            $results[] = [\n                \'service_id\' => $serviceId,\n                \'result\' => \'MISSED_NO_AVAILABLE_AIRCRAFT\',\n                \'scheduled_departure_at_utc\' => $scheduledDeparture,\n                \'origin_airport_icao_code\' => $service[\'origin_airport_icao_code\'] ?? null,\n            ];\n            continue;\n        }\n\n        $pilots = dispatch_fetch_pilots_for_aircraft_model($pdo, $companyId, (string)$aircraft[\'model_code\']);\n\n        if (count($pilots) < 2) {\n            $results[] = [\n                \'service_id\' => $serviceId,\n                \'result\' => \'BLOCKED_INSUFFICIENT_CREW\',\n                \'available_pilots\' => count($pilots),\n                \'scheduled_departure_at_utc\' => $scheduledDeparture,\n            ];\n            continue;\n        }\n\n        $technician = dispatch_fetch_best_technician($pdo, $companyId);\n        $flight = icaro_start_scheduled_service_flight(\n            $pdo,\n            $companyId,\n            $service,\n            $aircraft,\n            $pilots,\n            $technician,\n            $scheduledDeparture,\n            $flightDateUtc\n        );\n\n        $results[] = [\n            \'service_id\' => $serviceId,\n            \'result\' => \'DISPATCHED\',\n            \'flight_instance_id\' => $flight[\'flight_instance_id\'],\n            \'flight_code\' => $flight[\'flight_code\'],\n            \'aircraft_id\' => (int)$aircraft[\'aircraft_id\'],\n            \'scheduled_departure_at_utc\' => $scheduledDeparture,\n        ];\n    }\n\n    complete_due_flights($pdo, $companyId);\n\n    return [\n        \'status\' => \'OK\',\n        \'processed_count\' => count($results),\n        \'results\' => $results,\n    ];\n}\n\nfunction icaro_fetch_due_scheduled_services(PDO $pdo, int $companyId, int $windowMinutes, bool $devForce): array\n{\n    $nowTs = time();\n    $today = gmdate(\'Y-m-d\', $nowTs);\n\n    $stmt = $pdo->prepare("\n        SELECT\n          ss.id AS service_id,\n          ss.company_id,\n          ss.air_route_id,\n          ss.service_code,\n          ss.flight_route_code,\n          ss.service_type,\n          ss.recurrence_type,\n          ss.scheduled_departure_time_utc,\n          ss.service_status,\n          ss.preferred_aircraft_model_id,\n          ss.compatible_aircraft_model_codes,\n          ss.required_aircraft_class AS service_required_aircraft_class,\n          ss.base_ticket_price,\n          ss.currency_code,\n          ss.auto_dispatch_enabled,\n          ss.allow_backup_aircraft,\n          ss.allow_extra_flights,\n          ar.route_code,\n          ar.route_public_code,\n          ar.origin_airport_icao_code,\n          ar.destination_airport_icao_code,\n          ar.required_aircraft_class,\n          ar.planned_distance_km,\n          ar.estimated_block_minutes\n        FROM scheduled_services ss\n        JOIN air_routes ar ON ar.id = ss.air_route_id\n        WHERE ss.company_id = :company_id\n          AND ss.service_status = \'ACTIVE\'\n          AND ar.status = \'ACTIVE\'\n          AND UPPER(COALESCE(ss.service_type, \'SCHEDULED\')) = \'SCHEDULED\'\n          AND COALESCE(ss.auto_dispatch_enabled, 1) = 1\n          AND ss.scheduled_departure_time_utc IS NOT NULL\n        ORDER BY ss.scheduled_departure_time_utc, ss.id\n    ");\n    $stmt->execute([\'company_id\' => $companyId]);\n\n    $due = [];\n\n    foreach ($stmt->fetchAll() as $row) {\n        $scheduledDeparture = $today . \' \' . (string)$row[\'scheduled_departure_time_utc\'];\n        $departureTs = strtotime($scheduledDeparture . \' UTC\');\n\n        if ($departureTs === false) {\n            continue;\n        }\n\n        if (!$devForce && $departureTs > $nowTs) {\n            continue;\n        }\n\n        if (!$devForce && $departureTs < ($nowTs - ($windowMinutes * 60))) {\n            continue;\n        }\n\n        $row[\'scheduled_departure_at_utc\'] = gmdate(\'Y-m-d H:i:s\', $departureTs);\n        $due[] = $row;\n    }\n\n    return $due;\n}\n\n/**\n * Manual "start now" flights must not consume the daily automatic schedule.\n */\nfunction icaro_already_auto_processed_service_date(PDO $pdo, int $companyId, int $serviceId, string $flightDateUtc): bool\n{\n    $stmt = $pdo->prepare("\n        SELECT COUNT(*)\n        FROM scheduled_flight_instances\n        WHERE company_id = :company_id\n          AND scheduled_service_id = :service_id\n          AND flight_date_utc = :flight_date_utc\n          AND status <> \'CANCELLED\'\n          AND dispatch_status = :dispatch_status\n    ");\n    $stmt->execute([\n        \'company_id\' => $companyId,\n        \'service_id\' => $serviceId,\n        \'flight_date_utc\' => $flightDateUtc,\n        \'dispatch_status\' => ICARO_AUTO_DISPATCH_STATUS,\n    ]);\n\n    return (int)$stmt->fetchColumn() > 0;\n}\n\nfunction icaro_start_scheduled_service_flight(\n    PDO $pdo,\n    int $companyId,\n    array $service,\n    array $aircraft,\n    array $pilots,\n    ?array $technician,\n    string $scheduledDeparture,\n    string $flightDateUtc\n): array {\n    $flightCode = icaro_next_flight_instance_code($pdo, $companyId);\n    $durationMinutes = max(20, (int)($service[\'estimated_block_minutes\'] ?? 60));\n    $actualDeparture = gmdate(\'Y-m-d H:i:s\');\n    $scheduledArrival = gmdate(\n        \'Y-m-d H:i:s\',\n        strtotime($scheduledDeparture . \' UTC\') + ($durationMinutes * 60)\n    );\n\n    $capacity = max(1, (int)($aircraft[\'passenger_capacity_standard\'] ?? 1));\n    $loadFactor = random_int(55, 100);\n    $passengerCount = min($capacity, max(1, (int)floor($capacity * $loadFactor / 100)));\n    $ticketPrice = (float)($service[\'base_ticket_price\'] ?? 0);\n    $revenue = $passengerCount * $ticketPrice;\n    $blockHours = $durationMinutes / 60.0;\n    $fuelCost = $blockHours * (float)($aircraft[\'fuel_burn_kg_per_hour\'] ?? 0) * 1.20;\n    $maintenanceCost = $blockHours * (float)($aircraft[\'maintenance_cost_per_hour\'] ?? 0);\n    $staffCost = ((float)($pilots[0][\'salary_per_flight\'] ?? 0)) + ((float)($pilots[1][\'salary_per_flight\'] ?? 0));\n    $operatingCost = $fuelCost + $maintenanceCost + $staffCost;\n    $profit = $revenue - $operatingCost;\n\n    $columns = icaro_table_columns($pdo, \'scheduled_flight_instances\');\n    $values = [];\n\n    icaro_put($values, $columns, \'company_id\', $companyId);\n    icaro_put($values, $columns, \'air_route_id\', (int)($service[\'air_route_id\'] ?? 0));\n    icaro_put($values, $columns, \'scheduled_service_id\', (int)$service[\'service_id\']);\n    icaro_put($values, $columns, \'flight_code\', $flightCode);\n    icaro_put($values, $columns, \'flight_date_utc\', $flightDateUtc);\n    icaro_put($values, $columns, \'flight_operation_type\', \'SCHEDULED\');\n    icaro_put($values, $columns, \'status\', \'IN_FLIGHT\');\n    icaro_put($values, $columns, \'dispatch_status\', ICARO_AUTO_DISPATCH_STATUS);\n    icaro_put($values, $columns, \'backup_used\', 0);\n    icaro_put($values, $columns, \'origin_airport_icao_code\', $service[\'origin_airport_icao_code\']);\n    icaro_put($values, $columns, \'destination_airport_icao_code\', $service[\'destination_airport_icao_code\']);\n    icaro_put($values, $columns, \'required_aircraft_class\', $service[\'required_aircraft_class\'] ?? $service[\'service_required_aircraft_class\'] ?? \'LIGHT_COMMERCIAL\');\n    icaro_put($values, $columns, \'preferred_aircraft_model_id\', $service[\'preferred_aircraft_model_id\'] ?? null);\n    icaro_put($values, $columns, \'aircraft_id\', (int)$aircraft[\'aircraft_id\']);\n    icaro_put($values, $columns, \'planned_aircraft_id\', (int)$aircraft[\'aircraft_id\']);\n    icaro_put($values, $columns, \'dispatch_aircraft_id\', (int)$aircraft[\'aircraft_id\']);\n    icaro_put($values, $columns, \'pilot_1_staff_id\', (int)$pilots[0][\'staff_id\']);\n    icaro_put($values, $columns, \'pilot_2_staff_id\', (int)$pilots[1][\'staff_id\']);\n    icaro_put($values, $columns, \'technician_staff_id\', $technician ? (int)$technician[\'staff_id\'] : null);\n    icaro_put($values, $columns, \'passenger_capacity\', $capacity);\n    icaro_put($values, $columns, \'passenger_count\', $passengerCount);\n    icaro_put($values, $columns, \'load_factor_percent\', number_format(($passengerCount / $capacity) * 100, 2, \'.\', \'\'));\n    icaro_put($values, $columns, \'ticket_price\', number_format($ticketPrice, 2, \'.\', \'\'));\n    icaro_put($values, $columns, \'passenger_revenue\', number_format($revenue, 2, \'.\', \'\'));\n    icaro_put($values, $columns, \'fuel_cost\', number_format($fuelCost, 2, \'.\', \'\'));\n    icaro_put($values, $columns, \'maintenance_cost\', number_format($maintenanceCost, 2, \'.\', \'\'));\n    icaro_put($values, $columns, \'staff_cost\', number_format($staffCost, 2, \'.\', \'\'));\n    icaro_put($values, $columns, \'total_operating_cost\', number_format($operatingCost, 2, \'.\', \'\'));\n    icaro_put($values, $columns, \'profit_amount\', number_format($profit, 2, \'.\', \'\'));\n    icaro_put($values, $columns, \'currency_code\', $service[\'currency_code\'] ?? \'EUR\');\n    icaro_put($values, $columns, \'scheduled_departure_at_utc\', $scheduledDeparture);\n    icaro_put($values, $columns, \'actual_departure_at_utc\', $actualDeparture);\n    icaro_put($values, $columns, \'scheduled_arrival_at_utc\', $scheduledArrival);\n    icaro_put($values, $columns, \'actual_arrival_at_utc\', null);\n\n    $flightInstanceId = icaro_insert_dynamic($pdo, \'scheduled_flight_instances\', $values);\n\n    $pdo->prepare("\n        UPDATE company_aircraft\n        SET status = \'IN_FLIGHT\',\n            current_airport_icao_code = :destination\n        WHERE id = :aircraft_id\n          AND company_id = :company_id\n    ")->execute([\n        \'destination\' => $service[\'destination_airport_icao_code\'],\n        \'aircraft_id\' => (int)$aircraft[\'aircraft_id\'],\n        \'company_id\' => $companyId,\n    ]);\n\n    return [\n        \'flight_instance_id\' => $flightInstanceId,\n        \'flight_code\' => $flightCode,\n    ];\n}\n\nfunction icaro_next_flight_instance_code(PDO $pdo, int $companyId): string\n{\n    $base = time();\n    $candidate = \'IO-\' . $base;\n    $suffix = 0;\n    $stmt = $pdo->prepare("\n        SELECT COUNT(*)\n        FROM scheduled_flight_instances\n        WHERE company_id = :company_id\n          AND flight_code = :flight_code\n    ");\n\n    while (true) {\n        $code = $suffix === 0 ? $candidate : $candidate . \'-\' . $suffix;\n        $stmt->execute([\n            \'company_id\' => $companyId,\n            \'flight_code\' => $code,\n        ]);\n\n        if ((int)$stmt->fetchColumn() === 0) {\n            return $code;\n        }\n\n        $suffix++;\n    }\n}\n\nfunction icaro_table_columns(PDO $pdo, string $tableName): array\n{\n    $stmt = $pdo->prepare("\n        SELECT COLUMN_NAME\n        FROM information_schema.COLUMNS\n        WHERE TABLE_SCHEMA = DATABASE()\n          AND TABLE_NAME = :table_name\n    ");\n    $stmt->execute([\'table_name\' => $tableName]);\n\n    return array_flip(array_map(static fn ($row) => $row[\'COLUMN_NAME\'], $stmt->fetchAll()));\n}\n\nfunction icaro_put(array &$values, array $columns, string $column, mixed $value): void\n{\n    if (isset($columns[$column])) {\n        $values[$column] = $value;\n    }\n}\n\nfunction icaro_insert_dynamic(PDO $pdo, string $tableName, array $values): int\n{\n    $columns = array_keys($values);\n    $quoted = array_map(static fn ($column) => "`{$column}`", $columns);\n    $placeholders = array_map(static fn ($column) => ":{$column}", $columns);\n\n    $sql = "INSERT INTO {$tableName} (" . implode(\', \', $quoted) . ") VALUES (" . implode(\', \', $placeholders) . ")";\n    $stmt = $pdo->prepare($sql);\n\n    foreach ($values as $column => $value) {\n        $stmt->bindValue(":{$column}", $value);\n    }\n\n    $stmt->execute();\n\n    return (int)$pdo->lastInsertId();\n}\n'
PROCESS_DUE_CONTENT = "<?php\ndeclare(strict_types=1);\n\nrequire __DIR__ . '/../../lib/bootstrap.php';\nrequire __DIR__ . '/../../lib/session.php';\nrequire_once __DIR__ . '/../../lib/scheduled-service-dispatcher.php';\n\nif ($_SERVER['REQUEST_METHOD'] !== 'POST') {\n    json_response(['error' => 'METHOD_NOT_ALLOWED'], 405);\n}\n\n$session = require_auth_session();\n$companyId = (int)$session['company_id'];\n$payload = read_json_body();\n\n$windowMinutes = max(1, min(240, (int)($payload['window_minutes'] ?? 120)));\n$devForce = (bool)($payload['dev_force_due'] ?? false);\n\n$pdo = db();\n\ntry {\n    $pdo->beginTransaction();\n\n    $result = process_due_scheduled_services($pdo, $companyId, $windowMinutes, $devForce);\n\n    $pdo->commit();\n\n    json_response($result);\n} catch (Throwable $exception) {\n    if ($pdo->inTransaction()) {\n        $pdo->rollBack();\n    }\n\n    json_response([\n        'error' => 'PROCESS_DUE_SCHEDULED_SERVICES_FAILED',\n        'message' => $exception->getMessage(),\n    ], 500);\n}\n"

def read(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path}")
    return path.read_text(encoding="utf-8")

def write(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")

def patch_active_flights() -> None:
    content = read(ACTIVE_FLIGHTS)

    require_line = "require_once __DIR__ . '/../../lib/scheduled-service-dispatcher.php';\n"
    if require_line not in content:
        needle = "require __DIR__ . '/../../lib/flight-completion.php';\n"
        if needle not in content:
            raise RuntimeError("Unable to find flight-completion require in active.php")
        content = content.replace(needle, needle + require_line, 1)

    old = "complete_due_flights(db(), $companyId);"
    new = """$pdo = db();

if ($_SERVER['REQUEST_METHOD'] === 'GET') {
    try {
        $pdo->beginTransaction();
        process_due_scheduled_services($pdo, (int)$companyId, 240, false);
        $pdo->commit();
    } catch (Throwable $exception) {
        if ($pdo->inTransaction()) {
            $pdo->rollBack();
        }

        /*
         * The map must remain usable even if automatic dispatch fails.
         * The active flight layer will simply keep showing currently active flights.
         */
    }
}

complete_due_flights($pdo, $companyId);"""

    if "process_due_scheduled_services($pdo, (int)$companyId, 240, false);" not in content:
        if old not in content:
            raise RuntimeError("Unable to find complete_due_flights call in active.php")
        content = content.replace(old, new, 1)

    content = content.replace("$stmt = db()->prepare(", "$stmt = $pdo->prepare(")
    write(ACTIVE_FLIGHTS, content)

def patch_flight_layer_refresh() -> None:
    content = read(FLIGHT_LAYER)

    if "const ICARO_FLIGHT_REFRESH_MS" not in content:
        content = content.replace(
            "let icaroSelectedFlightPathLayer = null;\n",
            "let icaroSelectedFlightPathLayer = null;\nconst ICARO_FLIGHT_REFRESH_MS = 5000;\n",
            1
        )

    content = content.replace("setInterval(refreshIcaroFlights, 15000);", "setInterval(refreshIcaroFlights, ICARO_FLIGHT_REFRESH_MS);")

    if "document.addEventListener(\"visibilitychange\"" not in content:
        needle = "  setInterval(refreshIcaroFlights, ICARO_FLIGHT_REFRESH_MS);\n"
        content = content.replace(
            needle,
            needle + """\n  document.addEventListener("visibilitychange", () => {
    if (!document.hidden) {
      refreshIcaroFlights();
    }
  });

  window.addEventListener("focus", refreshIcaroFlights);
""",
            1
        )

    write(FLIGHT_LAYER, content)

def main() -> None:
    DISPATCHER_LIB.parent.mkdir(parents=True, exist_ok=True)
    write(DISPATCHER_LIB, DISPATCHER_LIB_CONTENT)
    write(PROCESS_DUE, PROCESS_DUE_CONTENT)
    patch_active_flights()
    patch_flight_layer_refresh()

    print("Patched map auto-dispatch refresh v6.")
    print("- Added shared scheduled-service dispatcher")
    print("- process-due-routes.php now uses the shared dispatcher")
    print("- active.php now dispatches due scheduled services before returning active flights")
    print("- flight-layer.js refreshes active flights every 5 seconds and on focus/visibility return")

if __name__ == "__main__":
    main()
