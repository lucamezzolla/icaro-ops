<?php
declare(strict_types=1);

require __DIR__ . '/../../lib/bootstrap.php';

$region = trim((string)($_GET['region'] ?? ''));

if ($region === '') {
    json_response(['error' => 'MISSING_REGION'], 422);
}

$stmt = db()->prepare("
    SELECT DISTINCT
      country_id,
      country_name
    FROM v_starting_base_airports
    WHERE world_region_code = :region
    ORDER BY country_name
");

$stmt->execute(['region' => $region]);

json_response($stmt->fetchAll());
