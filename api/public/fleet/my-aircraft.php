<?php
declare(strict_types=1);

require __DIR__ . '/../../lib/bootstrap.php';

$companyId = filter_input(INPUT_GET, 'companyId', FILTER_VALIDATE_INT);

if (!$companyId) {
    json_response(['error' => 'INVALID_COMPANY_ID'], 422);
}

$stmt = db()->prepare("
    SELECT *
    FROM v_company_fleet
    WHERE company_id = :company_id
    ORDER BY status, manufacturer, model_name, registration_code
");

$stmt->execute(['company_id' => $companyId]);

json_response(array_map(static function (array $row): array {
    return [
        'company_aircraft_id' => (int)$row['company_aircraft_id'],
        'company_id' => (int)$row['company_id'],
        'manufacturer' => $row['manufacturer'],
        'model_name' => $row['model_name'],
        'model_code' => $row['model_code'],
        'operation_role' => $row['operation_role'],
        'aircraft_category' => $row['aircraft_category'],
        'image_asset_path' => $row['image_asset_path'] ?? null,
        'registration_code' => $row['registration_code'],
        'manufacture_year' => (int)$row['manufacture_year'],
        'ownership_status' => $row['ownership_status'],
        'acquisition_type' => $row['acquisition_type'],
        'purchase_price' => $row['purchase_price'],
        'current_market_value' => $row['current_market_value'],
        'currency_code' => $row['currency_code'],
        'home_base_icao_code' => $row['home_base_icao_code'],
        'current_airport_icao_code' => $row['current_airport_icao_code'],
        'condition_percent' => $row['condition_percent'],
        'airframe_hours' => $row['airframe_hours'],
        'cycles_count' => (int)$row['cycles_count'],
        'status' => $row['status'],
        'is_available_for_sale' => (bool)$row['is_available_for_sale'],
        'asking_price' => $row['asking_price'],
        'passenger_capacity_standard' => (int)$row['passenger_capacity_standard'],
        'cargo_capacity_kg' => (int)$row['cargo_capacity_kg'],
        'range_km' => (int)$row['range_km'],
        'required_runway_m' => (int)$row['required_runway_m'],
    ];
}, $stmt->fetchAll()));
