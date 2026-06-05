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

if ($ticketPrice < 0) {
    json_response(['error' => 'INVALID_TICKET_PRICE'], 422);
}

$pdo = db();

$companyStmt = $pdo->prepare("
    SELECT currency_code
    FROM companies
    WHERE id = :company_id
    LIMIT 1
");
$companyStmt->execute(['company_id' => $companyId]);
$company = $companyStmt->fetch() ?: ['currency_code' => 'EUR'];

$originAirport = fetch_airport($pdo, $origin);
$destinationAirport = fetch_airport($pdo, $destination);

if (!$originAirport || !$destinationAirport) {
    json_response(['error' => 'AIRPORT_NOT_FOUND'], 404);
}

if (
    $originAirport['latitude'] === null ||
    $originAirport['longitude'] === null ||
    $destinationAirport['latitude'] === null ||
    $destinationAirport['longitude'] === null
) {
    json_response(['error' => 'AIRPORT_COORDINATES_MISSING'], 409);
}

/*
 * Development rule:
 * Current early-game route preview uses the Cessna 208B as reference aircraft.
 * Later this endpoint can accept aircraft_model_id or route aircraft.
 */
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

$cruiseSpeed = max(1.0, (float)$model['cruise_speed_kmh']);
$durationMinutes = max(20, (int)ceil(($distanceKm / $cruiseSpeed) * 60 + 15));
$blockHours = $durationMinutes / 60.0;

$capacity = (int)$model['passenger_capacity_standard'];
$fuelPricePerKg = 1.15;

$fuelCost = (float)$model['fuel_burn_kg_per_hour'] * $blockHours * $fuelPricePerKg;
$maintenanceCost = (float)$model['maintenance_cost_per_hour'] * $blockHours;

/*
 * Abstract crew cost model:
 *
 * Crew cost per flight =
 *   leg fee
 * + hourly rate * block hours
 * + revenue share
 *
 * daily_retainer is NOT charged to each flight.
 * It will belong to Finance daily operating costs.
 */
$crew = fetch_reference_pilots($pdo, $companyId);
$crewBaseCost = 0.0;

foreach ($crew as $pilot) {
    $crewBaseCost += (float)$pilot['salary_per_flight'];
    $crewBaseCost += (float)$pilot['hourly_rate'] * $blockHours;
}

$estimates = [];
foreach ([
    'low' => 0.55,
    'expected' => 0.75,
    'high' => 1.00,
] as $key => $loadFactor) {
    $passengers = max(1, min($capacity, (int)floor($capacity * $loadFactor)));
    $revenue = $passengers * $ticketPrice;

    $crewRevenueShare = 0.0;
    foreach ($crew as $pilot) {
        $crewRevenueShare += $revenue * ((float)$pilot['revenue_share_percent'] / 100.0);
    }

    $staffCost = $crewBaseCost + $crewRevenueShare;
    $totalCost = $fuelCost + $maintenanceCost + $staffCost;

    $estimates[$key] = [
        'load_factor_percent' => (int)round($loadFactor * 100),
        'passengers' => $passengers,
        'revenue' => money($revenue),
        'fuel_cost' => money($fuelCost),
        'maintenance_cost' => money($maintenanceCost),
        'staff_cost' => money($staffCost),
        'total_operating_cost' => money($totalCost),
        'profit' => money($revenue - $totalCost),
    ];
}

$expectedTotalCost = (float)$estimates['expected']['total_operating_cost'];
$breakEvenPassengers = $ticketPrice > 0 ? (int)ceil($expectedTotalCost / $ticketPrice) : null;

$suggestedTicket = suggest_ticket_price(
    $expectedTotalCost,
    max(1, (int)$estimates['expected']['passengers']),
    0.18
);

json_response([
    'origin_airport_icao_code' => $origin,
    'destination_airport_icao_code' => $destination,
    'planned_distance_km' => money($distanceKm),
    'planned_duration_minutes' => $durationMinutes,
    'block_hours' => money($blockHours),
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
    'ticket_price' => money($ticketPrice),
    'fuel_price_per_kg' => money($fuelPricePerKg),
    'cost_model' => [
        'crew_cost_formula' => 'leg_fee + hourly_rate * block_hours + revenue_share',
        'daily_retainer_note' => 'Daily retainers are company fixed costs and are not charged to each flight.',
        'crew_base_cost_before_revenue_share' => money($crewBaseCost),
        'selected_reference_pilots' => array_map(static function (array $pilot): array {
            return [
                'id' => (int)$pilot['id'],
                'display_name' => $pilot['display_name'],
                'leg_fee' => $pilot['salary_per_flight'],
                'hourly_rate' => $pilot['hourly_rate'],
                'revenue_share_percent' => $pilot['revenue_share_percent'],
            ];
        }, $crew),
    ],
    'costs' => [
        'fuel_cost' => $estimates['expected']['fuel_cost'],
        'maintenance_cost' => $estimates['expected']['maintenance_cost'],
        'staff_cost' => $estimates['expected']['staff_cost'],
        'total_operating_cost' => $estimates['expected']['total_operating_cost'],
    ],
    'estimates' => $estimates,
    'break_even_passengers' => $breakEvenPassengers,
    'suggested_ticket_price' => money($suggestedTicket),
    'recommendation' => recommendation($breakEvenPassengers, $capacity, (float)$estimates['expected']['profit']),
]);

function fetch_airport(PDO $pdo, string $icao): ?array
{
    $stmt = $pdo->prepare("
        SELECT icao_code, name, latitude, longitude
        FROM airports
        WHERE icao_code = :icao
        LIMIT 1
    ");
    $stmt->execute(['icao' => $icao]);
    $row = $stmt->fetch();

    return $row ?: null;
}

function fetch_reference_pilots(PDO $pdo, int $companyId): array
{
    $hasHourlyRate = column_exists($pdo, 'company_staff', 'hourly_rate');

    $hourlyExpr = $hasHourlyRate
        ? 's.hourly_rate'
        : 'GREATEST(60.00, s.salary_per_flight / 3) AS hourly_rate';

    $stmt = $pdo->prepare("
        SELECT
          s.id,
          s.display_name,
          s.salary_per_flight,
          {$hourlyExpr},
          s.revenue_share_percent
        FROM company_staff s
        WHERE s.company_id = :company_id
          AND s.staff_role = 'PILOT'
          AND s.employment_status = 'ACTIVE'
          AND EXISTS (
            SELECT 1
            FROM company_staff_licenses l
            WHERE l.company_staff_id = s.id
              AND l.license_code = 'CPL'
          )
          AND EXISTS (
            SELECT 1
            FROM company_staff_licenses l
            WHERE l.company_staff_id = s.id
              AND l.license_code = 'C208_TYPE'
          )
        ORDER BY s.reliability_score DESC, s.fatigue_score ASC, s.id
        LIMIT 2
    ");
    $stmt->execute(['company_id' => $companyId]);

    return $stmt->fetchAll();
}

function column_exists(PDO $pdo, string $tableName, string $columnName): bool
{
    $stmt = $pdo->prepare("
        SELECT COUNT(*)
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = :table_name
          AND COLUMN_NAME = :column_name
    ");
    $stmt->execute([
        'table_name' => $tableName,
        'column_name' => $columnName,
    ]);

    return (int)$stmt->fetchColumn() > 0;
}

function suggest_ticket_price(float $expectedCost, int $expectedPassengers, float $targetMargin): float
{
    $raw = ($expectedCost * (1.0 + $targetMargin)) / max(1, $expectedPassengers);

    if ($raw < 80) {
        return ceil($raw / 5) * 5;
    }

    if ($raw < 250) {
        return ceil($raw / 10) * 10;
    }

    return ceil($raw / 25) * 25;
}

function recommendation(?int $breakEvenPassengers, int $capacity, float $expectedProfit): string
{
    if ($breakEvenPassengers === null) {
        return 'Set a ticket price to calculate break-even.';
    }

    if ($breakEvenPassengers > $capacity) {
        return 'Ticket price is probably too low for this aircraft/route.';
    }

    if ($expectedProfit < 0) {
        return 'Possible only with high load factor or higher ticket price.';
    }

    if ($breakEvenPassengers >= max(1, (int)floor($capacity * 0.85))) {
        return 'Economically tight: profitable only with strong passenger demand.';
    }

    return 'Economically possible with enough passengers.';
}

function haversine_km(float $lat1, float $lon1, float $lat2, float $lon2): float
{
    $earthRadiusKm = 6371.0;
    $dLat = deg2rad($lat2 - $lat1);
    $dLon = deg2rad($lon2 - $lon1);

    $a = sin($dLat / 2) ** 2
        + cos(deg2rad($lat1))
        * cos(deg2rad($lat2))
        * sin($dLon / 2) ** 2;

    $c = 2 * atan2(sqrt($a), sqrt(1 - $a));

    return $earthRadiusKm * $c;
}

function money(float $value): string
{
    return number_format($value, 2, '.', '');
}
