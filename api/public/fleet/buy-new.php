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
$aircraftModelId = (int)($payload['aircraft_model_id'] ?? 0);
$deliveryAirportIcao = strtoupper(trim((string)($payload['delivery_airport_icao_code'] ?? '')));

if ($aircraftModelId <= 0) {
    json_response(['error' => 'VALIDATION_ERROR', 'message' => 'aircraft_model_id is required.'], 422);
}

if (!preg_match('/^[A-Z0-9]{4}$/', $deliveryAirportIcao)) {
    json_response([
        'error' => 'INVALID_DELIVERY_AIRPORT',
        'message' => 'Select a valid delivery airport before buying this aircraft.',
    ], 422);
}

$pdo = db();

try {
    $pdo->beginTransaction();

    $companyStmt = $pdo->prepare("
        SELECT id, company_name, currency_code, budget_amount, base_airport_icao_code
        FROM companies
        WHERE id = :company_id
        LIMIT 1
        FOR UPDATE
    ");
    $companyStmt->execute(['company_id' => $companyId]);
    $company = $companyStmt->fetch();

    if (!$company) {
        $pdo->rollBack();
        json_response(['error' => 'COMPANY_NOT_FOUND'], 404);
    }

    $airportStmt = $pdo->prepare("
        SELECT icao_code, iata_code, name, city, latitude, longitude
        FROM airports
        WHERE icao_code = :icao
        LIMIT 1
    ");
    $airportStmt->execute(['icao' => $deliveryAirportIcao]);
    $deliveryAirport = $airportStmt->fetch();

    if (!$deliveryAirport) {
        $pdo->rollBack();
        json_response([
            'error' => 'DELIVERY_AIRPORT_NOT_FOUND',
            'message' => 'The selected delivery airport was not found.',
        ], 404);
    }

    $priceColumn = first_existing_column($pdo, 'aircraft_models', [
        'new_purchase_price',
        'base_purchase_price',
        'new_price',
        'purchase_price',
        'estimated_new_price',
        'catalog_price',
        'price_amount',
        'new_cost_amount'
    ]);

    if ($priceColumn === null) {
        $pdo->rollBack();
        json_response([
            'error' => 'AIRCRAFT_PRICE_COLUMN_NOT_FOUND',
            'message' => 'No supported aircraft price column was found in aircraft_models.',
        ], 500);
    }

    $modelStmt = $pdo->prepare("
        SELECT
          id,
          manufacturer,
          model_name,
          model_code,
          icao_type_code,
          COALESCE({$priceColumn}, 0) AS new_purchase_price,
          COALESCE(currency_code, :company_currency_code) AS currency_code
        FROM aircraft_models
        WHERE id = :aircraft_model_id
        LIMIT 1
    ");
    $modelStmt->execute([
        'aircraft_model_id' => $aircraftModelId,
        'company_currency_code' => $company['currency_code'],
    ]);
    $model = $modelStmt->fetch();

    if (!$model) {
        $pdo->rollBack();
        json_response(['error' => 'AIRCRAFT_MODEL_NOT_FOUND'], 404);
    }

    $price = (float)$model['new_purchase_price'];
    $budget = (float)$company['budget_amount'];

    if ($budget < $price) {
        $pdo->rollBack();
        json_response([
            'error' => 'INSUFFICIENT_FUNDS',
            'message' => 'Company budget is not enough to buy this aircraft.',
            'required_amount' => number_format($price, 2, '.', ''),
            'current_budget' => number_format($budget, 2, '.', ''),
            'missing_amount' => number_format(max(0, $price - $budget), 2, '.', ''),
        ], 409);
    }

    $registrationCode = generate_registration_code($pdo, $companyId);

    $insert = $pdo->prepare("
        INSERT INTO company_aircraft (
          company_id,
          aircraft_model_id,
          registration_code,
          serial_number,
          manufacture_year,
          ownership_status,
          acquisition_type,
          purchase_price,
          current_market_value,
          currency_code,
          home_base_icao_code,
          current_airport_icao_code,
          condition_percent,
          airframe_hours,
          cycles_count,
          status,
          is_available_for_sale
        ) VALUES (
          :company_id,
          :aircraft_model_id,
          :registration_code,
          :serial_number,
          YEAR(UTC_DATE()),
          'OWNED',
          'NEW_PURCHASE',
          :purchase_price,
          :current_market_value,
          :currency_code,
          :home_base,
          :current_airport,
          100.00,
          0.00,
          0,
          'AVAILABLE',
          FALSE
        )
    ");

    $insert->execute([
        'company_id' => $companyId,
        'aircraft_model_id' => $aircraftModelId,
        'registration_code' => $registrationCode,
        'serial_number' => 'IO-SN-' . $registrationCode,
        'purchase_price' => number_format($price, 2, '.', ''),
        'current_market_value' => number_format($price * 0.92, 2, '.', ''),
        'currency_code' => $company['currency_code'],
        'home_base' => $deliveryAirportIcao,
        'current_airport' => $deliveryAirportIcao,
    ]);

    $aircraftId = (int)$pdo->lastInsertId();

    $budgetUpdate = $pdo->prepare("
        UPDATE companies
        SET budget_amount = budget_amount - :price
        WHERE id = :company_id
    ");
    $budgetUpdate->execute([
        'price' => number_format($price, 2, '.', ''),
        'company_id' => $companyId,
    ]);

    $pdo->commit();

    json_response([
        'company_aircraft_id' => $aircraftId,
        'registration_code' => $registrationCode,
        'manufacturer' => $model['manufacturer'],
        'model_name' => $model['model_name'],
        'model_code' => $model['model_code'],
        'icao_type_code' => $model['icao_type_code'],
        'purchase_price' => number_format($price, 2, '.', ''),
        'currency_code' => $company['currency_code'],
        'purchase_rule' => 'BUDGET_ONLY',
        'delivery_airport' => [
            'icao_code' => $deliveryAirport['icao_code'],
            'iata_code' => $deliveryAirport['iata_code'] ?? null,
            'name' => $deliveryAirport['name'],
            'city' => $deliveryAirport['city'] ?? null,
        ],
    ], 201);
} catch (Throwable $exception) {
    if ($pdo->inTransaction()) {
        $pdo->rollBack();
    }

    json_response([
        'error' => 'DATABASE_ERROR',
        'message' => 'Unable to buy aircraft.',
        'debug_message' => $exception->getMessage(),
    ], 500);
}

function first_existing_column(PDO $pdo, string $tableName, array $candidates): ?string
{
    $stmt = $pdo->prepare("
        SELECT COLUMN_NAME
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = :table_name
    ");
    $stmt->execute(['table_name' => $tableName]);

    $columns = array_flip(array_map(static fn ($row) => $row['COLUMN_NAME'], $stmt->fetchAll()));

    foreach ($candidates as $candidate) {
        if (isset($columns[$candidate])) {
            return '`' . str_replace('`', '``', $candidate) . '`';
        }
    }

    return null;
}

function generate_registration_code(PDO $pdo, int $companyId): string
{
    $stmt = $pdo->prepare("
        SELECT COUNT(*) + 1
        FROM company_aircraft
        WHERE company_id = :company_id
    ");
    $stmt->execute(['company_id' => $companyId]);
    $next = (int)$stmt->fetchColumn();

    return 'IO-' . str_pad((string)$companyId, 3, '0', STR_PAD_LEFT) . '-' . str_pad((string)$next, 3, '0', STR_PAD_LEFT);
}
