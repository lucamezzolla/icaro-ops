<?php
declare(strict_types=1);

require __DIR__ . '/../../lib/bootstrap.php';
require __DIR__ . '/../../lib/session.php';

$session = require_auth_session();
$companyId = (int)$session['company_id'];
$pdo = db();

$pageSize = 10;
$page = filter_input(INPUT_GET, 'page', FILTER_VALIDATE_INT);

if (!$page || $page < 1) {
    $page = 1;
}

$totalStmt = $pdo->prepare("
    SELECT COUNT(*)
    FROM scheduled_flight_instances
    WHERE company_id = :company_id
");
$totalStmt->execute(['company_id' => $companyId]);
$totalFlights = (int)$totalStmt->fetchColumn();

$totalPages = max(1, (int)ceil($totalFlights / $pageSize));

if ($page > $totalPages) {
    $page = $totalPages;
}

$offset = ($page - 1) * $pageSize;

$stmt = $pdo->prepare("
    SELECT
      f.id AS flight_id, f.route_id, f.company_id, f.aircraft_id, f.flight_code, f.flight_date_utc,
      f.origin_airport_icao_code, f.destination_airport_icao_code,
      f.scheduled_departure_at_utc, f.scheduled_arrival_at_utc,
      f.actual_departure_at_utc, f.actual_arrival_at_utc,
      f.status, f.passenger_capacity, f.passenger_count, f.load_factor_percent,
      f.ticket_price, f.passenger_revenue, f.fuel_cost, f.maintenance_cost,
      f.staff_cost, f.total_operating_cost, f.profit_amount, f.currency_code,
      ca.registration_code, am.manufacturer, am.model_name, am.model_code, am.icao_type_code
    FROM scheduled_flight_instances f
    LEFT JOIN company_aircraft ca ON ca.id = f.aircraft_id
    LEFT JOIN aircraft_models am ON am.id = ca.aircraft_model_id
    WHERE f.company_id = :company_id
    ORDER BY COALESCE(f.actual_departure_at_utc, f.scheduled_departure_at_utc) DESC, f.id DESC
    LIMIT :limit_rows OFFSET :offset_rows
");
$stmt->bindValue(':company_id', $companyId, PDO::PARAM_INT);
$stmt->bindValue(':limit_rows', $pageSize, PDO::PARAM_INT);
$stmt->bindValue(':offset_rows', $offset, PDO::PARAM_INT);
$stmt->execute();
$flights = $stmt->fetchAll();

$summaryStmt = $pdo->prepare("
    SELECT
      COUNT(*) AS total_flights,
      SUM(CASE WHEN status = 'COMPLETED' THEN 1 ELSE 0 END) AS completed_flights,
      SUM(CASE WHEN status = 'IN_FLIGHT' THEN 1 ELSE 0 END) AS in_flight_count,
      COALESCE(SUM(profit_amount), 0) AS total_profit_amount,
      MAX(currency_code) AS currency_code
    FROM scheduled_flight_instances
    WHERE company_id = :company_id
");
$summaryStmt->execute(['company_id' => $companyId]);
$summary = $summaryStmt->fetch() ?: [];

json_response([
    'summary' => [
        'total_flights' => (int)($summary['total_flights'] ?? 0),
        'completed_flights' => (int)($summary['completed_flights'] ?? 0),
        'in_flight_count' => (int)($summary['in_flight_count'] ?? 0),
        'total_profit_amount' => $summary['total_profit_amount'] ?? '0.00',
        'currency_code' => $summary['currency_code'] ?: 'EUR',
    ],
    'pagination' => [
        'page' => $page,
        'page_size' => $pageSize,
        'total_records' => $totalFlights,
        'total_pages' => $totalPages,
        'has_previous' => $page > 1,
        'has_next' => $page < $totalPages,
    ],
    'flights' => array_map(static function (array $row): array {
        return [
            'flight_id' => (int)$row['flight_id'],
            'route_id' => (int)$row['route_id'],
            'aircraft_id' => (int)$row['aircraft_id'],
            'flight_code' => $row['flight_code'],
            'flight_date_utc' => $row['flight_date_utc'],
            'origin_airport_icao_code' => $row['origin_airport_icao_code'],
            'destination_airport_icao_code' => $row['destination_airport_icao_code'],
            'scheduled_departure_at_utc' => $row['scheduled_departure_at_utc'],
            'scheduled_arrival_at_utc' => $row['scheduled_arrival_at_utc'],
            'actual_departure_at_utc' => $row['actual_departure_at_utc'],
            'actual_arrival_at_utc' => $row['actual_arrival_at_utc'],
            'status' => $row['status'],
            'passenger_capacity' => (int)$row['passenger_capacity'],
            'passenger_count' => (int)$row['passenger_count'],
            'load_factor_percent' => (int)$row['load_factor_percent'],
            'ticket_price' => $row['ticket_price'],
            'passenger_revenue' => $row['passenger_revenue'],
            'fuel_cost' => $row['fuel_cost'],
            'maintenance_cost' => $row['maintenance_cost'],
            'staff_cost' => $row['staff_cost'],
            'total_operating_cost' => $row['total_operating_cost'],
            'profit_amount' => $row['profit_amount'],
            'currency_code' => $row['currency_code'],
            'registration_code' => $row['registration_code'],
            'manufacturer' => $row['manufacturer'],
            'model_name' => $row['model_name'],
            'model_code' => $row['model_code'],
            'icao_type_code' => $row['icao_type_code'],
        ];
    }, $flights),
]);
