<?php
declare(strict_types=1);

require __DIR__ . '/../../lib/bootstrap.php';
require __DIR__ . '/../../lib/session.php';
require_once __DIR__ . '/../../lib/aircraft-type-rating.php';

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    json_response(['error' => 'METHOD_NOT_ALLOWED'], 405);
}

$session = require_auth_session();
$companyId = (int)$session['company_id'];
$payload = read_json_body();

$origin = strtoupper(trim((string)($payload['origin_airport_icao_code'] ?? '')));
$destination = strtoupper(trim((string)($payload['destination_airport_icao_code'] ?? '')));
$requestedTicketPrice = (float)($payload['ticket_price'] ?? $payload['base_ticket_price'] ?? 0);
$selectedModelCodes = normalize_selected_model_codes($payload['selected_aircraft_model_codes'] ?? $payload['aircraft_model_codes'] ?? []);

if (!preg_match('/^[A-Z0-9]{4}$/', $origin) || !preg_match('/^[A-Z0-9]{4}$/', $destination)) {
    json_response(['error' => 'INVALID_AIRPORT_CODE'], 422);
}

if ($origin === $destination) {
    json_response(['error' => 'INVALID_ROUTE'], 422);
}

if ($requestedTicketPrice < 0) {
    json_response(['error' => 'INVALID_TICKET_PRICE'], 422);
}

if (!$selectedModelCodes) {
    json_response([
        'error' => 'NO_AIRCRAFT_MODELS_SELECTED',
        'message' => 'Select at least one owned airplane model before previewing economics.',
    ], 422);
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
$currencyCode = (string)($company['currency_code'] ?? 'EUR');

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

$models = fetch_owned_models_by_code($pdo, $companyId, $selectedModelCodes);

if (count($models) !== count($selectedModelCodes)) {
    json_response([
        'error' => 'AIRCRAFT_MODEL_NOT_OWNED',
        'message' => 'One or more selected airplane models are not owned by your company.',
    ], 422);
}

$distanceKm = haversine_km(
    (float)$originAirport['latitude'],
    (float)$originAirport['longitude'],
    (float)$destinationAirport['latitude'],
    (float)$destinationAirport['longitude']
);

$initialPreviews = [];
foreach ($models as $model) {
    $initialPreviews[] = build_aircraft_preview($pdo, $companyId, $model, $distanceKm, 0.0);
}

$pricingPreview = select_pricing_preview($initialPreviews);
$suggestedTicket = suggest_market_ticket_price_for_load(
    (float)$pricingPreview['costs']['total_operating_cost_raw'],
    max(1, (int)$pricingPreview['expected_passengers']),
    75,
    $pricingPreview['aircraft'],
    0.18
);

$effectiveTicketPrice = $requestedTicketPrice > 0 ? $requestedTicketPrice : $suggestedTicket;

$aircraftPreviews = [];
foreach ($models as $model) {
    $aircraftPreviews[] = build_aircraft_preview($pdo, $companyId, $model, $distanceKm, $effectiveTicketPrice);
}

$selectedPreview = select_pricing_preview($aircraftPreviews);
$breakEvenPassengers = $effectiveTicketPrice > 0
    ? (int)ceil(((float)$selectedPreview['costs']['total_operating_cost_raw']) / $effectiveTicketPrice)
    : null;

json_response([
    'origin_airport_icao_code' => $origin,
    'destination_airport_icao_code' => $destination,
    'origin_airport_name' => $originAirport['name'] ?? '',
    'destination_airport_name' => $destinationAirport['name'] ?? '',
    'planned_distance_km' => money($distanceKm),
    'planned_duration_minutes' => (int)$selectedPreview['planned_duration_minutes'],
    'block_hours' => money((float)$selectedPreview['block_hours_raw']),
    'currency_code' => $currencyCode,
    'requested_ticket_price' => money($requestedTicketPrice),
    'ticket_price' => money($effectiveTicketPrice),
    'effective_ticket_price' => money($effectiveTicketPrice),
    'suggested_ticket_price' => money($suggestedTicket),
    'fuel_price_per_kg' => money(1.20),
    'selected_aircraft_count' => count($aircraftPreviews),
    'aircraft' => $selectedPreview['aircraft'],
    'aircraft_previews' => array_map('public_aircraft_preview', $aircraftPreviews),
    'passenger_capacity' => (int)$selectedPreview['passenger_capacity'],
    'costs' => public_costs($selectedPreview['costs']),
    'load_factor_scenarios' => $selectedPreview['load_factor_scenarios'],
    'demand_scenarios' => $selectedPreview['demand_scenarios'],
    'estimates' => legacy_estimates($selectedPreview['load_factor_scenarios']),
    'break_even_passengers' => $breakEvenPassengers,
    'break_even_ticket_at_expected_load' => money((float)$selectedPreview['break_even_ticket_at_expected_load_raw']),
    'cost_model' => [
        'crew_cost_formula' => 'pilot_1_salary_per_flight + pilot_2_salary_per_flight',
        'fuel_note' => 'Fuel is estimated with the same 1.20 unit price used by current dispatch calculations.',
        'maintenance_note' => 'Maintenance reserve is the aircraft hourly maintenance cost multiplied by estimated block hours.',
        'fixed_cost_note' => 'Daily retainers and company fixed costs are not charged to this single-flight preview.',
        'market_pricing_note' => 'Market recommended ticket uses the 75% load scenario as reference, then adjusts by expected demand, seat scarcity and aircraft prestige.',
        'passenger_demand_note' => 'Passenger forecasts are scenario-based: crisis, weak market, normal market, strong market and boom adjust expected load by demand climate, ticket price and aircraft prestige.',
        'selected_reference_pilots' => $selectedPreview['pilots'],
        'qualified_pilots_found' => (int)$selectedPreview['qualified_pilots_found'],
        'required_pilots' => 2,
    ],
    'recommendation' => recommendation($breakEvenPassengers, (int)$selectedPreview['passenger_capacity'], (float)$selectedPreview['expected_profit_raw']),
]);

function normalize_selected_model_codes(mixed $value): array
{
    if (is_string($value)) {
        $value = explode(',', $value);
    }

    if (!is_array($value)) {
        return [];
    }

    $codes = [];

    foreach ($value as $code) {
        $code = strtoupper(trim((string)$code));

        if ($code !== '' && preg_match('/^[A-Z0-9_]+$/', $code)) {
            $codes[] = $code;
        }
    }

    return array_values(array_unique($codes));
}

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

function fetch_owned_models_by_code(PDO $pdo, int $companyId, array $modelCodes): array
{
    if (!$modelCodes) {
        return [];
    }

    $placeholders = implode(',', array_fill(0, count($modelCodes), '?'));

    $stmt = $pdo->prepare("
        SELECT
          am.id,
          am.model_code,
          am.icao_type_code,
          am.manufacturer,
          am.model_name,
          am.passenger_capacity_standard,
          am.range_km,
          am.cruise_speed_kmh,
          am.fuel_burn_kg_per_hour,
          am.maintenance_cost_per_hour
        FROM aircraft_models am
        WHERE am.model_code IN ({$placeholders})
          AND EXISTS (
            SELECT 1
            FROM company_aircraft ca
            WHERE ca.company_id = ?
              AND ca.aircraft_model_id = am.id
          )
        ORDER BY FIELD(am.model_code, {$placeholders})
    ");

    $params = array_merge($modelCodes, [$companyId], $modelCodes);
    $stmt->execute($params);

    return $stmt->fetchAll();
}

function build_aircraft_preview(PDO $pdo, int $companyId, array $model, float $distanceKm, float $ticketPrice): array
{
    $cruiseSpeed = max(1.0, (float)($model['cruise_speed_kmh'] ?? 340));
    $durationMinutes = max(20, (int)ceil(($distanceKm / $cruiseSpeed) * 60 + 15));
    $blockHours = $durationMinutes / 60.0;
    $capacity = max(1, (int)($model['passenger_capacity_standard'] ?? 1));

    $fuelCost = $blockHours * (float)($model['fuel_burn_kg_per_hour'] ?? 0) * 1.20;
    $maintenanceCost = $blockHours * (float)($model['maintenance_cost_per_hour'] ?? 0);

    $pilots = fetch_reference_pilots($pdo, $companyId, (string)$model['model_code']);
    $staffCost = 0.0;
    foreach (array_slice($pilots, 0, 2) as $pilot) {
        $staffCost += (float)($pilot['salary_per_flight'] ?? 0);
    }

    $totalCost = $fuelCost + $maintenanceCost + $staffCost;
    $expectedPassengers = max(1, min($capacity, (int)floor($capacity * 0.75)));
    $breakEvenTicketExpected = $totalCost / max(1, $expectedPassengers);
    $marketReferenceTicket = suggest_market_ticket_price_for_load(
        $totalCost,
        $expectedPassengers,
        75,
        $model,
        0.18
    );

    $scenarios = [];
    foreach ([25, 50, 75, 90, 100] as $loadFactorPercent) {
        $passengers = max(1, min($capacity, (int)floor($capacity * ($loadFactorPercent / 100))));
        $revenue = $passengers * $ticketPrice;
        $profit = $revenue - $totalCost;
        $breakEvenTicket = $totalCost / max(1, $passengers);
        $marketRecommendedTicket = suggest_market_ticket_price_for_load(
            $totalCost,
            $expectedPassengers,
            $loadFactorPercent,
            $model,
            0.18
        );
        $marketRevenue = $passengers * $marketRecommendedTicket;
        $marketProfit = $marketRevenue - $totalCost;

        $scenarios[] = [
            'load_factor_percent' => $loadFactorPercent,
            'passengers' => $passengers,
            'revenue' => money($revenue),
            'fuel_cost' => money($fuelCost),
            'maintenance_cost' => money($maintenanceCost),
            'staff_cost' => money($staffCost),
            'total_operating_cost' => money($totalCost),
            'profit' => money($profit),
            'break_even_ticket_price' => money($breakEvenTicket),
            'market_recommended_ticket_price' => money($marketRecommendedTicket),
            'market_revenue' => money($marketRevenue),
            'market_profit' => money($marketProfit),
            'market_signal' => market_signal($marketProfit, $marketRecommendedTicket, $breakEvenTicket, $loadFactorPercent),
            'demand_multiplier' => money(demand_multiplier_for_load($loadFactorPercent)),
        ];
    }

    return [
        'aircraft' => [
            'id' => (int)$model['id'],
            'manufacturer' => $model['manufacturer'],
            'model_name' => $model['model_name'],
            'model_code' => $model['model_code'],
            'icao_type_code' => $model['icao_type_code'],
            'passenger_capacity_standard' => $capacity,
            'cruise_speed_kmh' => $model['cruise_speed_kmh'],
            'fuel_burn_kg_per_hour' => $model['fuel_burn_kg_per_hour'],
            'maintenance_cost_per_hour' => $model['maintenance_cost_per_hour'],
        ],
        'passenger_capacity' => $capacity,
        'planned_duration_minutes' => $durationMinutes,
        'block_hours_raw' => $blockHours,
        'expected_passengers' => $expectedPassengers,
        'expected_profit_raw' => ($expectedPassengers * $ticketPrice) - $totalCost,
        'break_even_ticket_at_expected_load_raw' => $breakEvenTicketExpected,
        'market_reference_ticket_price_raw' => $marketReferenceTicket,
        'costs' => [
            'fuel_cost_raw' => $fuelCost,
            'maintenance_cost_raw' => $maintenanceCost,
            'staff_cost_raw' => $staffCost,
            'total_operating_cost_raw' => $totalCost,
        ],
        'load_factor_scenarios' => $scenarios,
        'demand_scenarios' => build_passenger_demand_scenarios($capacity, $ticketPrice, $marketReferenceTicket, $totalCost, $model, $distanceKm),
        'pilots' => array_map(static function (array $pilot): array {
            return [
                'id' => (int)$pilot['id'],
                'display_name' => $pilot['display_name'],
                'salary_per_flight' => $pilot['salary_per_flight'],
            ];
        }, array_slice($pilots, 0, 2)),
        'qualified_pilots_found' => count($pilots),
    ];
}

function fetch_reference_pilots(PDO $pdo, int $companyId, string $modelCode): array
{
    $license = required_aircraft_type_rating($pdo, $modelCode);

    $sql = "
        SELECT
          s.id,
          s.display_name,
          s.salary_per_flight
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
    ";

    $params = ['company_id' => $companyId];

    if ($license !== null) {
        $sql .= "
          AND EXISTS (
            SELECT 1
            FROM company_staff_licenses l
            WHERE l.company_staff_id = s.id
              AND l.license_code = :license_code
          )
        ";
        $params['license_code'] = $license;
    }

    $sql .= " ORDER BY s.reliability_score DESC, s.fatigue_score ASC, s.id LIMIT 2";

    $stmt = $pdo->prepare($sql);
    $stmt->execute($params);

    return $stmt->fetchAll();
}


function build_passenger_demand_scenarios(
    int $capacity,
    float $ticketPrice,
    float $marketReferenceTicket,
    float $totalCost,
    array $aircraft,
    float $distanceKm
): array {
    $effectiveTicket = $ticketPrice > 0 ? $ticketPrice : $marketReferenceTicket;
    $referenceTicket = max(1.0, $marketReferenceTicket);
    $prestige = aircraft_prestige_multiplier($aircraft);

    $states = [
        ['code' => 'CRISIS', 'label' => 'Crisis', 'base_load' => 0.35, 'demand_index' => 0.55],
        ['code' => 'WEAK', 'label' => 'Weak market', 'base_load' => 0.55, 'demand_index' => 0.75],
        ['code' => 'NORMAL', 'label' => 'Normal market', 'base_load' => 0.72, 'demand_index' => 1.00],
        ['code' => 'STRONG', 'label' => 'Strong market', 'base_load' => 0.88, 'demand_index' => 1.20],
        ['code' => 'BOOM', 'label' => 'Full success / boom', 'base_load' => 0.98, 'demand_index' => 1.40],
    ];

    $distanceAdjustment = passenger_distance_load_adjustment($distanceKm);
    $priceRatio = $effectiveTicket / $referenceTicket;
    $pricePenalty = max(0.0, $priceRatio - 1.0);
    $priceDiscount = max(0.0, 1.0 - $priceRatio);
    $priceElasticity = passenger_price_elasticity($aircraft);

    $rows = [];
    foreach ($states as $state) {
        $prestigeAdjustment = ($prestige - 1.0) * 0.12;
        $loadFactor = (float)$state['base_load']
            + $distanceAdjustment
            + $prestigeAdjustment
            - ($pricePenalty * $priceElasticity)
            + ($priceDiscount * 0.10);

        $loadFactor = max(0.05, min(1.0, $loadFactor));
        $passengers = max(1, min($capacity, (int)floor($capacity * $loadFactor)));
        $revenue = $passengers * $effectiveTicket;
        $profit = $revenue - $totalCost;

        $rows[] = [
            'scenario_code' => $state['code'],
            'scenario_name' => $state['label'],
            'demand_index' => money((float)$state['demand_index']),
            'load_factor_percent' => money($loadFactor * 100.0),
            'passengers' => $passengers,
            'ticket_price' => money($effectiveTicket),
            'market_reference_ticket_price' => money($marketReferenceTicket),
            'revenue' => money($revenue),
            'total_operating_cost' => money($totalCost),
            'profit' => money($profit),
            'calculation_note' => passenger_calculation_note($state['label'], $priceRatio, $distanceAdjustment, $prestige),
        ];
    }

    return $rows;
}

function passenger_distance_load_adjustment(float $distanceKm): float
{
    if ($distanceKm < 300) {
        return -0.05;
    }

    if ($distanceKm > 6500) {
        return -0.04;
    }

    if ($distanceKm >= 900 && $distanceKm <= 3500) {
        return 0.03;
    }

    return 0.0;
}

function passenger_price_elasticity(array $aircraft): float
{
    $modelCode = strtoupper((string)($aircraft['model_code'] ?? ''));
    $icaoCode = strtoupper((string)($aircraft['icao_type_code'] ?? ''));
    $modelName = strtoupper((string)($aircraft['model_name'] ?? ''));

    if ($icaoCode === 'CONC' || str_contains($modelCode, 'CONC') || str_contains($modelName, 'CONCORDE')) {
        return 0.18;
    }

    return 0.32;
}

function passenger_calculation_note(string $stateLabel, float $priceRatio, float $distanceAdjustment, float $prestige): string
{
    $priceText = $priceRatio > 1.05
        ? 'ticket above market reference reduces demand'
        : ($priceRatio < 0.95 ? 'ticket below market reference supports demand' : 'ticket near market reference');

    $distanceText = $distanceAdjustment > 0
        ? 'route distance supports demand'
        : ($distanceAdjustment < 0 ? 'route distance slightly reduces demand' : 'neutral route distance');

    $prestigeText = $prestige > 1.01
        ? 'aircraft prestige supports demand'
        : 'standard aircraft prestige';

    return $stateLabel . ': ' . $priceText . '; ' . $distanceText . '; ' . $prestigeText . '.';
}

function select_pricing_preview(array $previews): array
{
    usort($previews, static function (array $a, array $b): int {
        return ((float)$b['costs']['total_operating_cost_raw']) <=> ((float)$a['costs']['total_operating_cost_raw']);
    });

    return $previews[0];
}

function public_aircraft_preview(array $preview): array
{
    return [
        'aircraft' => $preview['aircraft'],
        'passenger_capacity' => (int)$preview['passenger_capacity'],
        'planned_duration_minutes' => (int)$preview['planned_duration_minutes'],
        'block_hours' => money((float)$preview['block_hours_raw']),
        'costs' => public_costs($preview['costs']),
        'expected_passengers' => (int)$preview['expected_passengers'],
        'expected_profit' => money((float)$preview['expected_profit_raw']),
        'break_even_ticket_at_expected_load' => money((float)$preview['break_even_ticket_at_expected_load_raw']),
        'suggested_ticket_price' => money((float)$preview['market_reference_ticket_price_raw']),
        'load_factor_scenarios' => $preview['load_factor_scenarios'],
        'demand_scenarios' => $preview['demand_scenarios'],
        'qualified_pilots_found' => (int)$preview['qualified_pilots_found'],
    ];
}

function public_costs(array $costs): array
{
    return [
        'fuel_cost' => money((float)$costs['fuel_cost_raw']),
        'maintenance_cost' => money((float)$costs['maintenance_cost_raw']),
        'staff_cost' => money((float)$costs['staff_cost_raw']),
        'total_operating_cost' => money((float)$costs['total_operating_cost_raw']),
    ];
}

function legacy_estimates(array $scenarios): array
{
    $byPercent = [];
    foreach ($scenarios as $scenario) {
        $byPercent[(int)$scenario['load_factor_percent']] = $scenario;
    }

    return [
        'low' => $byPercent[50] ?? $scenarios[0],
        'expected' => $byPercent[75] ?? $scenarios[0],
        'high' => $byPercent[100] ?? $scenarios[array_key_last($scenarios)],
    ];
}

function suggest_ticket_price(float $expectedCost, int $expectedPassengers, float $targetMargin): float
{
    return round_ticket_price(($expectedCost * (1.0 + $targetMargin)) / max(1, $expectedPassengers));
}

function suggest_market_ticket_price_for_load(
    float $expectedCost,
    int $expectedPassengers,
    int $loadFactorPercent,
    array $aircraft,
    float $targetMargin
): float {
    $baseTicket = suggest_ticket_price($expectedCost, $expectedPassengers, $targetMargin);
    $raw = $baseTicket
        * demand_multiplier_for_load($loadFactorPercent)
        * aircraft_prestige_multiplier($aircraft);

    return round_ticket_price($raw);
}

function demand_multiplier_for_load(int $loadFactorPercent): float
{
    if ($loadFactorPercent >= 100) {
        return 1.45;
    }

    if ($loadFactorPercent >= 90) {
        return 1.30;
    }

    if ($loadFactorPercent >= 75) {
        return 1.15;
    }

    if ($loadFactorPercent >= 50) {
        return 1.00;
    }

    return 0.85;
}

function aircraft_prestige_multiplier(array $aircraft): float
{
    $modelCode = strtoupper((string)($aircraft['model_code'] ?? ''));
    $icaoCode = strtoupper((string)($aircraft['icao_type_code'] ?? ''));
    $modelName = strtoupper((string)($aircraft['model_name'] ?? ''));

    if ($icaoCode === 'CONC' || str_contains($modelCode, 'CONC') || str_contains($modelName, 'CONCORDE')) {
        return 1.35;
    }

    foreach (['A388', 'A380', 'B748', '748_', 'B744', 'B747', 'B77', 'B78', 'A359', 'A35', 'A346', 'A343'] as $needle) {
        if (str_contains($icaoCode, $needle) || str_contains($modelCode, $needle)) {
            return 1.08;
        }
    }

    return 1.00;
}

function market_signal(float $marketProfit, float $marketTicket, float $breakEvenTicket, int $loadFactorPercent): string
{
    if ($marketTicket < $breakEvenTicket) {
        return 'Weak demand / market price below break-even';
    }

    if ($marketProfit < 0) {
        return 'Risky demand / likely loss';
    }

    if ($loadFactorPercent >= 90) {
        return 'Strong demand / scarce seats';
    }

    if ($loadFactorPercent >= 75) {
        return 'Healthy demand';
    }

    if ($loadFactorPercent >= 50) {
        return 'Moderate demand';
    }

    return 'Weak demand / low occupancy';
}

function round_ticket_price(float $raw): float
{
    if ($raw < 80) {
        return ceil($raw / 5) * 5;
    }

    if ($raw < 250) {
        return ceil($raw / 10) * 10;
    }

    if ($raw < 1000) {
        return ceil($raw / 25) * 25;
    }

    return ceil($raw / 50) * 50;
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
