<?php
declare(strict_types=1);

require __DIR__ . '/../../lib/bootstrap.php';

$stmt = db()->query("
    SELECT DISTINCT
      world_region_code,
      world_region_name
    FROM v_starting_base_airports
    ORDER BY world_region_name
");

json_response($stmt->fetchAll());
