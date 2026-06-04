<?php
declare(strict_types=1);

require __DIR__ . '/../../lib/bootstrap.php';

$companyId = filter_input(INPUT_GET, 'companyId', FILTER_VALIDATE_INT);

if (!$companyId) {
    json_response(['error' => 'INVALID_COMPANY_ID'], 422);
}

$stmt = db()->prepare("
    SELECT
      co.id AS company_id,
      co.company_name,
      co.currency_code,
      co.budget_amount,
      co.reputation_score,
      co.base_airport_icao_code,

      p.first_name,
      p.last_name,
      p.nickname,

      wr.code AS world_region_code,
      wr.name AS world_region_name,
      c.id AS country_id,
      c.name AS country_name,

      a.icao_code,
      a.iata_code,
      a.name AS airport_name,
      a.city,
      a.location_name,
      a.subdivision_name,
      a.latitude,
      a.longitude,
      a.airport_type,
      a.service_category,

      v.base_tier,
      v.max_initial_aircraft_class,
      v.starting_base_score,
      v.local_passenger_demand_score,
      v.local_cargo_demand_score,
      v.tourism_score,
      v.business_score,
      v.competition_score,
      v.airport_fee_score,
      v.starting_difficulty,
      v.starting_base_note,

      acp.airport_size_tier,
      acp.max_player_bases,
      acp.max_rival_bases,
      acp.max_total_bases
    FROM companies co
    JOIN players p
      ON p.id = co.player_id
    JOIN airports a
      ON a.icao_code = co.base_airport_icao_code
    JOIN countries c
      ON c.id = a.country_id
    JOIN world_regions wr
      ON wr.code = c.world_region_code
    LEFT JOIN v_starting_base_airports v
      ON v.icao_code = a.icao_code
    LEFT JOIN airport_capacity_profiles acp
      ON acp.airport_icao_code = a.icao_code
    WHERE co.id = :company_id
    LIMIT 1
");

$stmt->execute(['company_id' => $companyId]);
$row = $stmt->fetch();

if (!$row) {
    json_response(['error' => 'COMPANY_NOT_FOUND'], 404);
}

$ownerName = trim((string)($row['first_name'] ?? '') . ' ' . (string)($row['last_name'] ?? ''));
if ($ownerName === '') {
    $ownerName = $row['nickname'] ?? '';
}

json_response([
    'company_id' => (int)$row['company_id'],
    'company_name' => $row['company_name'],
    'owner_name' => $ownerName,
    'first_name' => $row['first_name'],
    'last_name' => $row['last_name'],
    'currency_code' => $row['currency_code'],
    'budget_amount' => $row['budget_amount'],
    'reputation_score' => (int)$row['reputation_score'],
    'base_airport' => [
        'world_region_code' => $row['world_region_code'],
        'world_region_name' => $row['world_region_name'],
        'country_id' => (int)$row['country_id'],
        'country_name' => $row['country_name'],
        'icao_code' => $row['icao_code'],
        'iata_code' => $row['iata_code'],
        'airport_name' => $row['airport_name'],
        'city' => $row['city'],
        'location_name' => $row['location_name'],
        'subdivision_name' => $row['subdivision_name'],
        'latitude' => $row['latitude'],
        'longitude' => $row['longitude'],
        'airport_type' => $row['airport_type'],
        'service_category' => $row['service_category'],
        'base_tier' => $row['base_tier'] ?? 'UNCLASSIFIED',
        'max_initial_aircraft_class' => $row['max_initial_aircraft_class'],
        'starting_base_score' => isset($row['starting_base_score']) ? (int)$row['starting_base_score'] : null,
        'local_passenger_demand_score' => isset($row['local_passenger_demand_score']) ? (int)$row['local_passenger_demand_score'] : 0,
        'local_cargo_demand_score' => isset($row['local_cargo_demand_score']) ? (int)$row['local_cargo_demand_score'] : 0,
        'tourism_score' => isset($row['tourism_score']) ? (int)$row['tourism_score'] : 0,
        'business_score' => isset($row['business_score']) ? (int)$row['business_score'] : 0,
        'competition_score' => isset($row['competition_score']) ? (int)$row['competition_score'] : 0,
        'airport_fee_score' => isset($row['airport_fee_score']) ? (int)$row['airport_fee_score'] : 0,
        'starting_difficulty' => $row['starting_difficulty'] ?? 'UNKNOWN',
        'starting_base_note' => $row['starting_base_note'],
        'airport_size_tier' => $row['airport_size_tier'] ?? 'UNCLASSIFIED',
        'max_player_bases' => isset($row['max_player_bases']) ? (int)$row['max_player_bases'] : 1,
        'max_rival_bases' => isset($row['max_rival_bases']) ? (int)$row['max_rival_bases'] : 0,
        'max_total_bases' => isset($row['max_total_bases']) ? (int)$row['max_total_bases'] : 1,
    ],
]);
