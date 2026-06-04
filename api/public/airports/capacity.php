<?php
declare(strict_types=1);

require __DIR__ . '/../../lib/bootstrap.php';

$icao = strtoupper(trim((string)($_GET['icao'] ?? '')));

if (strlen($icao) !== 4) {
    json_response(['error' => 'INVALID_ICAO'], 422);
}

$stmt = db()->prepare("
    SELECT
      airport_icao_code,
      iata_code,
      airport_name,
      city,
      country_name,
      world_region_code,
      world_region_name,
      airport_size_tier,
      max_player_bases,
      max_rival_bases,
      max_total_bases,
      used_player_bases,
      used_rival_bases,
      used_total_bases,
      available_player_base_slots,
      available_rival_base_slots,
      available_total_base_slots,
      is_full,
      note
    FROM v_airport_base_capacity_status
    WHERE airport_icao_code = :icao
    LIMIT 1
");

$stmt->execute(['icao' => $icao]);
$row = $stmt->fetch();

if (!$row) {
    json_response(['error' => 'AIRPORT_NOT_FOUND'], 404);
}

json_response([
    'airport_icao_code' => $row['airport_icao_code'],
    'iata_code' => $row['iata_code'],
    'airport_name' => $row['airport_name'],
    'city' => $row['city'],
    'country_name' => $row['country_name'],
    'world_region_code' => $row['world_region_code'],
    'world_region_name' => $row['world_region_name'],
    'airport_size_tier' => $row['airport_size_tier'],
    'max_player_bases' => (int)$row['max_player_bases'],
    'max_rival_bases' => (int)$row['max_rival_bases'],
    'max_total_bases' => (int)$row['max_total_bases'],
    'used_player_bases' => (int)$row['used_player_bases'],
    'used_rival_bases' => (int)$row['used_rival_bases'],
    'used_total_bases' => (int)$row['used_total_bases'],
    'available_player_base_slots' => (int)$row['available_player_base_slots'],
    'available_rival_base_slots' => (int)$row['available_rival_base_slots'],
    'available_total_base_slots' => (int)$row['available_total_base_slots'],
    'is_full' => (bool)$row['is_full'],
    'note' => $row['note'],
]);
