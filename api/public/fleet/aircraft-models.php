<?php
declare(strict_types=1);

require __DIR__ . '/../../lib/bootstrap.php';

$companyId = filter_input(INPUT_GET, 'companyId', FILTER_VALIDATE_INT);

if (!$companyId) {
    json_response(['error' => 'INVALID_COMPANY_ID'], 422);
}

$companyStmt = db()->prepare("
    SELECT
      co.id,
      co.currency_code,
      co.budget_amount,
      co.reputation_score,
      co.base_airport_icao_code,
      a.name AS base_airport_name,
      a.airport_type,
      a.service_category,
      bc.max_aircraft_managed,
      bc.aircraft_owned_count,
      bc.free_managed_aircraft_slots
    FROM companies co
    JOIN airports a
      ON a.icao_code = co.base_airport_icao_code
    LEFT JOIN v_player_base_aircraft_capacity_status bc
      ON bc.company_id = co.id
     AND bc.airport_icao_code = co.base_airport_icao_code
    WHERE co.id = :company_id
    LIMIT 1
");

$companyStmt->execute(['company_id' => $companyId]);
$company = $companyStmt->fetch();

if (!$company) {
    json_response(['error' => 'COMPANY_NOT_FOUND'], 404);
}

$stmt = db()->query("
    SELECT *
    FROM v_active_aircraft_catalog
    ORDER BY unlock_reputation_score, new_purchase_price, manufacturer, model_name
");

$budget = (float)$company['budget_amount'];
$reputation = (int)$company['reputation_score'];
$freeSlots = (int)($company['free_managed_aircraft_slots'] ?? 0);

json_response(array_map(static function (array $row) use ($budget, $reputation, $freeSlots): array {
    $canBuy = true;
    $blockReason = null;

    if (!(bool)$row['is_available_new']) {
        $canBuy = false;
        $blockReason = 'New unavailable';
    } elseif ((bool)$row['is_endgame']) {
        $canBuy = false;
        $blockReason = 'Endgame';
    } elseif ($reputation < (int)$row['unlock_reputation_score']) {
        $canBuy = false;
        $blockReason = 'Reputation locked';
    } elseif ($freeSlots <= 0) {
        $canBuy = false;
        $blockReason = 'No fleet slots';
    } elseif ($budget < (float)$row['new_purchase_price']) {
        $canBuy = false;
        $blockReason = 'Not enough budget';
    }

    return [
        'aircraft_model_id' => (int)$row['aircraft_model_id'],
        'manufacturer' => $row['manufacturer'],
        'model_name' => $row['model_name'],
        'model_code' => $row['model_code'],
        'icao_type_code' => $row['icao_type_code'],
        'iata_type_code' => $row['iata_type_code'],
        'aircraft_family' => $row['aircraft_family'],
        'aircraft_category' => $row['aircraft_category'],
        'operation_role' => $row['operation_role'],
        'engine_type' => $row['engine_type'],
        'engine_count' => (int)$row['engine_count'],
        'crew_required_min' => (int)$row['crew_required_min'],
        'passenger_capacity_standard' => (int)$row['passenger_capacity_standard'],
        'passenger_capacity_max' => (int)$row['passenger_capacity_max'],
        'cargo_capacity_kg' => (int)$row['cargo_capacity_kg'],
        'range_km' => (int)$row['range_km'],
        'required_runway_m' => (int)$row['required_runway_m'],
        'new_purchase_price' => $row['new_purchase_price'],
        'lease_price_per_day' => $row['lease_price_per_day'],
        'currency_code' => $row['currency_code'],
        'unlock_reputation_score' => (int)$row['unlock_reputation_score'],
        'minimum_airport_size_tier' => $row['minimum_airport_size_tier'],
        'gameplay_notes' => $row['gameplay_notes'],
        'image_asset_path' => $row['image_asset_path'] ?? null,
        'can_buy' => $canBuy,
        'block_reason' => $blockReason,
    ];
}, $stmt->fetchAll()));
