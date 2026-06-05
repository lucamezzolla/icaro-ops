<?php
declare(strict_types=1);

require __DIR__ . '/../../lib/bootstrap.php';
require __DIR__ . '/../../lib/session.php';

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    json_response(['error' => 'METHOD_NOT_ALLOWED'], 405);
}

$session = require_auth_session();
$companyId = $session['company_id'];

$payload = read_json_body();
$aircraftModelId = (int)($payload['aircraft_model_id'] ?? 0);

if ($aircraftModelId <= 0) {
    json_response(['error' => 'VALIDATION_ERROR', 'message' => 'aircraft_model_id is required.'], 422);
}

$pdo = db();

try {
    $pdo->beginTransaction();

    $companyStmt = $pdo->prepare("
        SELECT
          id,
          company_name,
          currency_code,
          budget_amount,
          base_airport_icao_code
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

    $modelStmt = $pdo->prepare("
        SELECT
          id,
          manufacturer,
          model_name,
          model_code,
          icao_type_code,
          new_purchase_price,
          currency_code,
          is_available_new,
          is_active,
          is_endgame,
          unlock_reputation_score
        FROM aircraft_models
        WHERE id = :aircraft_model_id
        LIMIT 1
    ");
    $modelStmt->execute(['aircraft_model_id' => $aircraftModelId]);
    $model = $modelStmt->fetch();

    if (!$model || !(bool)$model['is_active']) {
        $pdo->rollBack();
        json_response(['error' => 'AIRCRAFT_MODEL_NOT_FOUND'], 404);
    }

    if (!(bool)$model['is_available_new'] || (bool)$model['is_endgame']) {
        $pdo->rollBack();
        json_response(['error' => 'AIRCRAFT_NOT_AVAILABLE_NEW'], 409);
    }

    $price = (float)$model['new_purchase_price'];
    $budget = (float)$company['budget_amount'];

    if ($budget < $price) {
        $pdo->rollBack();
        json_response([
            'error' => 'INSUFFICIENT_FUNDS',
            'message' => 'Company budget is not enough to buy this aircraft.',
        ], 409);
    }

    /*
     * Core gameplay rule:
     * every aircraft requires two active pilots.
     *
     * Technicians are NOT required to buy aircraft and are NOT flight crew.
     * They are managed separately for maintenance/repairs.
     */
    $aircraftCountStmt = $pdo->prepare("
        SELECT COUNT(*)
        FROM company_aircraft
        WHERE company_id = :company_id
          AND ownership_status IN ('OWNED', 'LEASED')
    ");
    $aircraftCountStmt->execute(['company_id' => $companyId]);
    $currentAircraftCount = (int)$aircraftCountStmt->fetchColumn();

    $requiredPilotsAfterPurchase = ($currentAircraftCount + 1) * 2;
    $typeLicense = required_pilot_type_license((string)$model['model_code']);

    $pilotCount = count_qualified_pilots($pdo, $companyId, $typeLicense);

    if ($pilotCount < $requiredPilotsAfterPurchase) {
        $pdo->rollBack();
        json_response([
            'error' => 'INSUFFICIENT_QUALIFIED_PILOTS',
            'message' => sprintf(
                'You need %d active qualified pilots after this purchase. Current qualified pilots: %d.',
                $requiredPilotsAfterPurchase,
                $pilotCount
            ),
            'required_pilots_after_purchase' => $requiredPilotsAfterPurchase,
            'current_qualified_pilots' => $pilotCount,
            'required_license' => $typeLicense,
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
        'home_base' => $company['base_airport_icao_code'],
        'current_airport' => $company['base_airport_icao_code'],
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
        'purchase_price' => number_format($price, 2, '.', ''),
        'currency_code' => $company['currency_code'],
        'required_pilots_after_purchase' => $requiredPilotsAfterPurchase,
        'current_qualified_pilots' => $pilotCount,
    ], 201);
} catch (Throwable $exception) {
    if ($pdo->inTransaction()) {
        $pdo->rollBack();
    }

    json_response([
        'error' => 'DATABASE_ERROR',
        'message' => 'Unable to buy aircraft.',
    ], 500);
}

function required_pilot_type_license(string $modelCode): ?string
{
    return match ($modelCode) {
        'C208B_GRAND_CARAVAN_EX' => 'C208_TYPE',
        'DHC6_TWIN_OTTER_400' => 'DHC6_TYPE',
        'ATR42_600' => 'ATR42_TYPE',
        default => null,
    };
}

function count_qualified_pilots(PDO $pdo, int $companyId, ?string $typeLicense): int
{
    $sql = "
        SELECT COUNT(*)
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

    if ($typeLicense !== null) {
        $sql .= "
          AND EXISTS (
            SELECT 1
            FROM company_staff_licenses l
            WHERE l.company_staff_id = s.id
              AND l.license_code = :type_license
          )
        ";
        $params['type_license'] = $typeLicense;
    }

    $stmt = $pdo->prepare($sql);
    $stmt->execute($params);

    return (int)$stmt->fetchColumn();
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
