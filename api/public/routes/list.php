<?php
declare(strict_types=1);

require __DIR__ . '/../../lib/bootstrap.php';
require __DIR__ . '/../../lib/session.php';

$session = require_auth_session();
$companyId = $session['company_id'];

$stmt = db()->prepare("
    SELECT *
    FROM v_company_routes
    WHERE company_id = :company_id
    ORDER BY scheduled_departure_time_utc, origin_airport_icao_code, destination_airport_icao_code
");

$stmt->execute(['company_id' => $companyId]);

json_response(array_map(static function (array $row): array {
    return [
        'route_id' => (int)$row['route_id'],
        'company_id' => (int)$row['company_id'],
        'aircraft_id' => (int)$row['aircraft_id'],
        'registration_code' => $row['registration_code'],
        'manufacturer' => $row['manufacturer'],
        'model_name' => $row['model_name'],
        'model_code' => $row['model_code'],
        'origin_airport_icao_code' => $row['origin_airport_icao_code'],
        'origin_airport_name' => $row['origin_airport_name'],
        'destination_airport_icao_code' => $row['destination_airport_icao_code'],
        'destination_airport_name' => $row['destination_airport_name'],
        'scheduled_departure_time_utc' => $row['scheduled_departure_time_utc'],
        'recurrence_type' => $row['recurrence_type'],
        'planned_distance_km' => $row['planned_distance_km'],
        'planned_duration_minutes' => (int)$row['planned_duration_minutes'],
        'ticket_price' => $row['ticket_price'],
        'currency_code' => $row['currency_code'],
        'status' => $row['status'],
        'pilot_1_name' => $row['pilot_1_name'],
        'pilot_2_name' => $row['pilot_2_name'],
        'technician_name' => $row['technician_name'],
    ];
}, $stmt->fetchAll()));
