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

$routeId = (int)($payload['route_id'] ?? 0);

if ($routeId <= 0) {
    json_response(['error' => 'VALIDATION_ERROR', 'message' => 'route_id is required.'], 422);
}

$pdo = db();

try {
    $pdo->beginTransaction();

    $routeStmt = $pdo->prepare("
        SELECT id, origin_airport_icao_code, destination_airport_icao_code
        FROM company_routes
        WHERE id = :route_id
          AND company_id = :company_id
        LIMIT 1
        FOR UPDATE
    ");
    $routeStmt->execute([
        'route_id' => $routeId,
        'company_id' => $companyId,
    ]);

    $route = $routeStmt->fetch();

    if (!$route) {
        $pdo->rollBack();
        json_response(['error' => 'ROUTE_NOT_FOUND'], 404);
    }

    $activeStmt = $pdo->prepare("
        SELECT COUNT(*)
        FROM scheduled_flight_instances
        WHERE route_id = :route_id
          AND status IN ('SCHEDULED', 'IN_FLIGHT')
    ");
    $activeStmt->execute(['route_id' => $routeId]);

    if ((int)$activeStmt->fetchColumn() > 0) {
        $pdo->rollBack();
        json_response([
            'error' => 'ROUTE_HAS_ACTIVE_FLIGHTS',
            'message' => 'This route has active/scheduled flights. Complete them before deleting the route.',
        ], 409);
    }

    $historyStmt = $pdo->prepare("
        SELECT COUNT(*)
        FROM scheduled_flight_instances
        WHERE route_id = :route_id
    ");
    $historyStmt->execute(['route_id' => $routeId]);
    $hasHistory = (int)$historyStmt->fetchColumn() > 0;

    if ($hasHistory) {
        $stmt = $pdo->prepare("
            UPDATE company_routes
            SET
              status = 'CANCELLED',
              auto_dispatch_enabled = FALSE,
              updated_at_utc = CURRENT_TIMESTAMP
            WHERE id = :route_id
              AND company_id = :company_id
        ");
        $stmt->execute([
            'route_id' => $routeId,
            'company_id' => $companyId,
        ]);

        $action = 'CANCELLED';
    } else {
        $stmt = $pdo->prepare("
            DELETE FROM company_routes
            WHERE id = :route_id
              AND company_id = :company_id
        ");
        $stmt->execute([
            'route_id' => $routeId,
            'company_id' => $companyId,
        ]);

        $action = 'DELETED';
    }

    $pdo->commit();

    json_response([
        'route_id' => $routeId,
        'action' => $action,
        'origin_airport_icao_code' => $route['origin_airport_icao_code'],
        'destination_airport_icao_code' => $route['destination_airport_icao_code'],
    ]);
} catch (Throwable $exception) {
    if ($pdo->inTransaction()) {
        $pdo->rollBack();
    }

    json_response(['error' => 'DATABASE_ERROR', 'message' => 'Unable to delete route.'], 500);
}
