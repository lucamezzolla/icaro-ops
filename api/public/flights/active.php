<?php
declare(strict_types=1);

require __DIR__ . '/../../lib/bootstrap.php';
require __DIR__ . '/../../lib/session.php';
require __DIR__ . '/../../lib/flight-completion.php';
require_once __DIR__ . '/../../lib/maintenance-engine.php';
require_once __DIR__ . '/../../lib/scheduled-service-dispatcher.php';

$session = require_auth_session();
$companyId = $session['company_id'];

$pdo = db();

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

complete_due_flights($pdo, $companyId);
complete_due_maintenance($pdo, (int)$companyId);

$stmt = $pdo->prepare("
    SELECT *
    FROM v_active_flights_map
    WHERE company_id = :company_id
    ORDER BY scheduled_departure_at_utc
");

$stmt->execute(['company_id' => $companyId]);

json_response(array_map(static function (array $row): array {
    return [
        'flight_instance_id' => (int)$row['flight_instance_id'],
        'route_id' => (int)$row['route_id'],
        'company_id' => (int)$row['company_id'],
        'company_name' => $row['company_name'],
        'aircraft_id' => (int)$row['aircraft_id'],
        'registration_code' => $row['registration_code'],
        'manufacturer' => $row['manufacturer'],
        'model_name' => $row['model_name'],
        'model_code' => $row['model_code'],
        'flight_code' => $row['flight_code'],
        'origin_airport_icao_code' => $row['origin_airport_icao_code'],
        'origin_airport_name' => $row['origin_airport_name'],
        'origin_latitude' => $row['origin_latitude'],
        'origin_longitude' => $row['origin_longitude'],
        'destination_airport_icao_code' => $row['destination_airport_icao_code'],
        'destination_airport_name' => $row['destination_airport_name'],
        'destination_latitude' => $row['destination_latitude'],
        'destination_longitude' => $row['destination_longitude'],
        'scheduled_departure_at_utc' => $row['scheduled_departure_at_utc'],
        'scheduled_arrival_at_utc' => $row['scheduled_arrival_at_utc'],
        'actual_departure_at_utc' => $row['actual_departure_at_utc'],
        'status' => $row['status'],
        'passenger_capacity' => (int)$row['passenger_capacity'],
        'passenger_count' => (int)$row['passenger_count'],
        'load_factor_percent' => $row['load_factor_percent'],
        'passenger_revenue' => $row['passenger_revenue'],
        'total_operating_cost' => $row['total_operating_cost'],
        'profit_amount' => $row['profit_amount'],
        'currency_code' => $row['currency_code'],
        'progress_percent' => (float)$row['progress_percent'],
    ];
}, $stmt->fetchAll()));
