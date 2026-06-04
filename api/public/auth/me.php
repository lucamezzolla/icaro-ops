<?php
declare(strict_types=1);

require __DIR__ . '/../../lib/bootstrap.php';
require __DIR__ . '/../../lib/session.php';

$session = require_auth_session();

$stmt = db()->prepare("
    SELECT
      p.id AS player_id,
      p.first_name,
      p.last_name,
      p.email,
      p.interface_language,
      co.id AS company_id,
      co.company_name,
      co.currency_code,
      co.budget_amount,
      co.reputation_score,
      co.base_airport_icao_code,
      a.name AS base_airport_name,
      a.iata_code AS base_airport_iata_code,
      c.name AS country_name,
      wr.name AS world_region_name
    FROM players p
    JOIN companies co
      ON co.player_id = p.id
    JOIN airports a
      ON a.icao_code = co.base_airport_icao_code
    JOIN countries c
      ON c.id = a.country_id
    JOIN world_regions wr
      ON wr.code = c.world_region_code
    WHERE p.id = :player_id
      AND co.id = :company_id
    LIMIT 1
");

$stmt->execute([
    'player_id' => $session['player_id'],
    'company_id' => $session['company_id'],
]);

$row = $stmt->fetch();

if (!$row) {
    start_app_session();
    $_SESSION = [];
    session_destroy();
    json_response(['error' => 'SESSION_COMPANY_NOT_FOUND'], 401);
}

json_response([
    'player_id' => (int)$row['player_id'],
    'first_name' => $row['first_name'],
    'last_name' => $row['last_name'],
    'owner_name' => trim((string)$row['first_name'] . ' ' . (string)$row['last_name']),
    'email' => $row['email'],
    'interface_language' => $row['interface_language'],
    'company_id' => (int)$row['company_id'],
    'company_name' => $row['company_name'],
    'currency_code' => $row['currency_code'],
    'budget_amount' => $row['budget_amount'],
    'reputation_score' => (int)$row['reputation_score'],
    'base_airport' => [
        'icao_code' => $row['base_airport_icao_code'],
        'iata_code' => $row['base_airport_iata_code'],
        'airport_name' => $row['base_airport_name'],
        'country_name' => $row['country_name'],
        'world_region_name' => $row['world_region_name'],
    ],
]);
