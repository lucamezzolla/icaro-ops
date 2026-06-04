<?php
declare(strict_types=1);

require __DIR__ . '/../../lib/bootstrap.php';

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    json_response(['error' => 'METHOD_NOT_ALLOWED'], 405);
}

$payload = read_json_body();

$companyAircraftId = (int)($payload['company_aircraft_id'] ?? 0);
$companyId = (int)($payload['company_id'] ?? 0);
$askingPrice = (float)($payload['asking_price'] ?? 0);

if ($companyAircraftId <= 0 || $companyId <= 0 || $askingPrice <= 0) {
    json_response(['error' => 'VALIDATION_ERROR', 'message' => 'company_aircraft_id, company_id and asking_price are required.'], 422);
}

$stmt = db()->prepare("
    UPDATE company_aircraft
    SET
      is_available_for_sale = TRUE,
      asking_price = :asking_price,
      status = CASE WHEN status = 'AVAILABLE' THEN 'FOR_SALE' ELSE status END
    WHERE id = :aircraft_id
      AND company_id = :company_id
      AND ownership_status = 'OWNED'
      AND status IN ('PARKED', 'AVAILABLE', 'FOR_SALE')
");

$stmt->execute([
    'asking_price' => $askingPrice,
    'aircraft_id' => $companyAircraftId,
    'company_id' => $companyId,
]);

if ($stmt->rowCount() === 0) {
    json_response(['error' => 'AIRCRAFT_NOT_LISTED', 'message' => 'Aircraft could not be listed for sale.'], 409);
}

json_response(['ok' => true]);
