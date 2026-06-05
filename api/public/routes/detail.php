<?php
declare(strict_types=1);

require __DIR__ . '/../../lib/bootstrap.php';
require __DIR__ . '/../../lib/session.php';

$session = require_auth_session();
$companyId = (int)$session['company_id'];
$routeId = filter_input(INPUT_GET, 'routeId', FILTER_VALIDATE_INT);

if (!$routeId) {
    json_response(['error' => 'INVALID_ROUTE_ID'], 422);
}

$stmt = db()->prepare("
    SELECT *
    FROM v_company_routes
    WHERE company_id = :company_id
      AND route_id = :route_id
    LIMIT 1
");
$stmt->execute([
    'company_id' => $companyId,
    'route_id' => $routeId,
]);
$route = $stmt->fetch();

if (!$route) {
    json_response(['error' => 'ROUTE_NOT_FOUND'], 404);
}

$flights = db()->prepare("
    SELECT id, flight_code, status, flight_date_utc, passenger_count, passenger_revenue, total_operating_cost, profit_amount, currency_code
    FROM scheduled_flight_instances
    WHERE company_id = :company_id
      AND route_id = :route_id
    ORDER BY id DESC
    LIMIT 20
");
$flights->execute([
    'company_id' => $companyId,
    'route_id' => $routeId,
]);

json_response([
    'route' => $route,
    'recent_flights' => $flights->fetchAll(),
]);
