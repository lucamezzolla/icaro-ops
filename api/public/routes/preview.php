<?php
declare(strict_types=1);

require __DIR__ . '/../../lib/bootstrap.php';
require __DIR__ . '/../../lib/session.php';

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    json_response(['error' => 'METHOD_NOT_ALLOWED'], 405);
}

$session = require_auth_session();
$companyId = (int)$session['company_id'];
$payload = read_json_body();

$origin = strtoupper(trim((string)($payload['origin_airport_icao_code'] ?? '')));
$destination = strtoupper(trim((string)($payload['destination_airport_icao_code'] ?? '')));
$ticketPrice = (float)($payload['ticket_price'] ?? 0);

if (!preg_match('/^[A-Z0-9]{4}$/', $origin) || !preg_match('/^[A-Z0-9]{4}$/', $destination)) {
    json_response(['error' => 'INVALID_AIRPORT_CODE'], 422);
}

if ($origin === $destination) {
    json_response(['error' => 'INVALID_ROUTE'], 422);
}

$pdo = db();

$companyStmt = $pdo->prepare("SELECT currency_code FROM companies WHERE id = :company_id LIMIT 1");
$companyStmt->execute(['company_id' => $companyId]);
$company = $companyStmt->fetch();

$originAirport = fetch_airport($pdo, $origin);
$destinationAirport = fetch_airport($pdo, $destination);

if (!$originAirport || !$destinationAirport) {
    json_response(['error' => 'AIRPORT_NOT_FOUND'], 404);
}

if ($originAirport['latitude'] === null || $originAirport['longitude'] === null || $destinationAirport['latitude'] === null || $destinationAirport['longitude'] === null) {
    json_response(['error' => 'AIRPORT_COORDINATES_MISSING'], 409);
}

$modelStmt = $pdo->prepare("
    SELECT *
    FROM aircraft_models
    WHERE model_code = 'C208B_GRAND_CARAVAN_EX'
    LIMIT 1
");
$modelStmt->execute();
$model = $modelStmt->fetch();

if (!$model) {
    json_response(['error' => 'AIRCRAFT_MODEL_NOT_FOUND'], 500);
}

$distanceKm = haversine_km(
    (float)$originAirport['latitude'],
    (float)$originAirport['longitude'],
    (float)$destinationAirport['latitude'],
    (float)$destinationAirport['longitude']
);

$durationMinutes = max(20, (int)ceil(($distanceKm / max(1, (float)$model['cruise_speed_kmh'])) * 60 + 15));
$durationHours = $durationMinutes / 60.0;

$capacity = (int)$model['passenger_capacity_standard'];
$fuelCost = (float)$model['fuel_burn_kg_per_hour'] * $durationHours * 1.15;
$maintenanceCost = (float)$model['maintenance_cost_per_hour'] * $durationHours;
$staffCost = estimate_staff_cost($pdo, $companyId, $ticketPrice * max(1, (int)floor($capacity * 0.75)));

$totalCost = $fuelCost + $maintenanceCost + $staffCost;

$estimates = [];
foreach (['low' => 0.55, 'expected' => 0.75, 'high' => 1.00] as $key => $factor) {
    $passengers = max(1, min($capacity, (int)floor($capacity * $factor)));
    $revenue = $passengers * $ticketPrice;
    $estimates[$key] = [
        'load_factor_percent' => (int)round($factor * 100),
        'passengers' => $passengers,
        'revenue' => number_format($revenue, 2, '.', ''),
        'profit' => number_format($revenue - $totalCost, 2, '.', ''),
    ];
}

$breakEven = $ticketPrice > 0 ? (int)ceil($totalCost / $ticketPrice) : null;

json_response([
    'origin_airport_icao_code' => $origin,
    'destination_airport_icao_code' => $destination,
    'planned_distance_km' => number_format($distanceKm, 2, '.', ''),
    'planned_duration_minutes' => $durationMinutes,
    'currency_code' => $company['currency_code'] ?? 'EUR',
    'aircraft' => [
        'manufacturer' => $model['manufacturer'],
        'model_name' => $model['model_name'],
        'model_code' => $model['model_code'],
        'passenger_capacity_standard' => (int)$model['passenger_capacity_standard'],
        'cruise_speed_kmh' => $model['cruise_speed_kmh'],
        'fuel_burn_kg_per_hour' => $model['fuel_burn_kg_per_hour'],
        'maintenance_cost_per_hour' => $model['maintenance_cost_per_hour'],
    ],
    'passenger_capacity' => $capacity,
    'ticket_price' => number_format($ticketPrice, 2, '.', ''),
    'costs' => [
        'fuel_cost' => number_format($fuelCost, 2, '.', ''),
        'maintenance_cost' => number_format($maintenanceCost, 2, '.', ''),
        'staff_cost' => number_format($staffCost, 2, '.', ''),
        'total_operating_cost' => number_format($totalCost, 2, '.', ''),
    ],
    'estimates' => $estimates,
    'break_even_passengers' => $breakEven,
    'recommendation' => ($breakEven !== null && $breakEven <= $capacity) ? 'Economically possible with enough passengers.' : 'Ticket price is probably too low for this aircraft/route.',
]);

function fetch_airport(PDO $pdo, string $icao): ?array
{
    $stmt = $pdo->prepare("SELECT icao_code, name, latitude, longitude FROM airports WHERE icao_code = :icao LIMIT 1");
    $stmt->execute(['icao' => $icao]);
    $row = $stmt->fetch();
    return $row ?: null;
}

function estimate_staff_cost(PDO $pdo, int $companyId, float $expectedRevenue): float
{
    $stmt = $pdo->prepare("
        SELECT salary_per_flight, revenue_share_percent
        FROM company_staff
        WHERE company_id = :company_id
          AND staff_role = 'PILOT'
          AND employment_status = 'ACTIVE'
        ORDER BY reliability_score DESC, fatigue_score ASC, id
        LIMIT 2
    ");
    $stmt->execute(['company_id' => $companyId]);
    $pilots = $stmt->fetchAll();

    $cost = 0.0;
    foreach ($pilots as $pilot) {
        $cost += (float)$pilot['salary_per_flight'];
        $cost += $expectedRevenue * ((float)$pilot['revenue_share_percent'] / 100.0);
    }

    return $cost;
}

function haversine_km(float $lat1, float $lon1, float $lat2, float $lon2): float
{
    $earthRadiusKm = 6371.0;
    $dLat = deg2rad($lat2 - $lat1);
    $dLon = deg2rad($lon2 - $lon1);
    $a = sin($dLat / 2) ** 2 + cos(deg2rad($lat1)) * cos(deg2rad($lat2)) * sin($dLon / 2) ** 2;
    $c = 2 * atan2(sqrt($a), sqrt(1 - $a));
    return $earthRadiusKm * $c;
}
