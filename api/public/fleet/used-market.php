<?php
declare(strict_types=1);

require __DIR__ . '/../../lib/bootstrap.php';

$companyId = filter_input(INPUT_GET, 'companyId', FILTER_VALIDATE_INT);

if (!$companyId) {
    json_response(['error' => 'INVALID_COMPANY_ID'], 422);
}

$stmt = db()->prepare("
    SELECT *
    FROM v_used_aircraft_market
    WHERE seller_company_id <> :company_id
    ORDER BY asking_price, manufacturer, model_name
    LIMIT 100
");

$stmt->execute(['company_id' => $companyId]);

json_response(array_map(static function (array $row): array {
    return [
        'company_aircraft_id' => (int)$row['company_aircraft_id'],
        'seller_company_id' => (int)$row['seller_company_id'],
        'seller_company_name' => $row['seller_company_name'],
        'registration_code' => $row['registration_code'],
        'manufacturer' => $row['manufacturer'],
        'model_name' => $row['model_name'],
        'model_code' => $row['model_code'],
        'icao_type_code' => $row['icao_type_code'],
        'aircraft_category' => $row['aircraft_category'],
        'operation_role' => $row['operation_role'],
        'image_asset_path' => $row['image_asset_path'] ?? null,
        'manufacture_year' => (int)$row['manufacture_year'],
        'condition_percent' => $row['condition_percent'],
        'airframe_hours' => $row['airframe_hours'],
        'cycles_count' => (int)$row['cycles_count'],
        'current_market_value' => $row['current_market_value'],
        'asking_price' => $row['asking_price'],
        'currency_code' => $row['currency_code'],
        'home_base_icao_code' => $row['home_base_icao_code'],
        'current_airport_icao_code' => $row['current_airport_icao_code'],
        'current_airport_name' => $row['current_airport_name'],
        'passenger_capacity_standard' => (int)$row['passenger_capacity_standard'],
        'cargo_capacity_kg' => (int)$row['cargo_capacity_kg'],
        'range_km' => (int)$row['range_km'],
        'required_runway_m' => (int)$row['required_runway_m'],
        'status' => $row['status'],
    ];
}, $stmt->fetchAll()));
