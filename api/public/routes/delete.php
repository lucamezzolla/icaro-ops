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

$serviceId = (int)($payload['service_id'] ?? $payload['route_id'] ?? 0);

if ($serviceId <= 0) {
    json_response(['error' => 'INVALID_SERVICE_ID'], 422);
}

$pdo = db();

try {
    $pdo->beginTransaction();

    $stmt = $pdo->prepare("
        SELECT id, service_code
        FROM scheduled_services
        WHERE id = :service_id
          AND company_id = :company_id
          AND service_status <> 'CANCELLED'
        LIMIT 1
        FOR UPDATE
    ");
    $stmt->execute([
        'service_id' => $serviceId,
        'company_id' => $companyId,
    ]);

    $service = $stmt->fetch();

    if (!$service) {
        $pdo->rollBack();
        json_response(['error' => 'SERVICE_NOT_FOUND'], 404);
    }

    $activeFlights = $pdo->prepare("
        SELECT COUNT(*)
        FROM scheduled_flight_instances
        WHERE company_id = :company_id
          AND scheduled_service_id = :service_id
          AND status IN ('SCHEDULED', 'BOARDING', 'IN_FLIGHT', 'DELAYED')
    ");
    $activeFlights->execute([
        'company_id' => $companyId,
        'service_id' => $serviceId,
    ]);

    if ((int)$activeFlights->fetchColumn() > 0) {
        $pdo->rollBack();
        json_response([
            'error' => 'SERVICE_HAS_ACTIVE_FLIGHTS',
            'message' => 'This flight route has active or pending flight instances and cannot be removed now.',
        ], 409);
    }

    $pdo->prepare("
        UPDATE scheduled_services
        SET service_status = 'CANCELLED'
        WHERE id = :service_id
          AND company_id = :company_id
    ")->execute([
        'service_id' => $serviceId,
        'company_id' => $companyId,
    ]);

    $pdo->commit();

    json_response([
        'status' => 'REMOVED',
        'service_id' => $serviceId,
        'service_code' => $service['service_code'],
        'message' => 'Flight route removed.',
    ]);
} catch (Throwable $exception) {
    if ($pdo->inTransaction()) {
        $pdo->rollBack();
    }

    json_response([
        'error' => 'SERVICE_REMOVE_FAILED',
        'message' => 'Unable to remove flight route.',
    ], 500);
}
