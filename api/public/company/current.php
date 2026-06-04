<?php
declare(strict_types=1);

require __DIR__ . '/../../lib/bootstrap.php';

$companyId = filter_input(INPUT_GET, 'companyId', FILTER_VALIDATE_INT);

if (!$companyId) {
    json_response(['error' => 'INVALID_COMPANY_ID'], 422);
}

/*
 * Do not depend exclusively on v_starting_base_airports here.
 * A company base must remain readable even if later balancing rules remove
 * that airport from the starting-base view.
 */
$stmt = db()->prepare("
    SELECT
      co.id AS company_id,
      co.company_name,
      co.currency_code,
      co.budget_amount,
      co.reputation_score,
      co.base_airport_icao_code,

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

      COALESCE(v.base_tier, 'BASE') AS base_tier,
      COALESCE(v.max_initial_aircraft_class, 'LIGHT_COMMERCIAL') AS max_initial_aircraft_class,
      COALESCE(v.starting_base_score, 0) AS starting_base_score,
      COALESCE(v.local_passenger_demand_score, 0) AS local_passenger_demand_score,
      COALESCE(v.local_cargo_demand_score, 0) AS local_cargo_demand_score,
      COALESCE(v.tourism_score, 0) AS tourism_score,
      COALESCE(v.business_score, 0) AS business_score,
      COALESCE(v.competition_score, 0) AS competition_score,
      COALESCE(v.airport_fee_score, 0) AS airport_fee_score,
      COALESCE(v.starting_difficulty, 'UNKNOWN') AS starting_difficulty,
      COALESCE(v.starting_base_note, 'Company base airport.') AS starting_base_note
    FROM companies co
    JOIN airports a
      ON a.icao_code = co.base_airport_icao_code
    JOIN countries c
      ON c.id = a.country_id
    JOIN world_regions wr
      ON wr.code = c.world_region_code
    LEFT JOIN v_starting_base_airports v
      ON v.icao_code = a.icao_code
    WHERE co.id = :company_id
    LIMIT 1
");

$stmt->execute(['company_id' => $companyId]);
$row = $stmt->fetch();

if (!$row) {
    json_response(['error' => 'COMPANY_NOT_FOUND'], 404);
}

json_response([
    'company_id' => (int)$row['company_id'],
    'company_name' => $row['company_name'],
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
        'base_tier' => $row['base_tier'],
        'max_initial_aircraft_class' => $row['max_initial_aircraft_class'],
        'starting_base_score' => (int)$row['starting_base_score'],
        'local_passenger_demand_score' => (int)$row['local_passenger_demand_score'],
        'local_cargo_demand_score' => (int)$row['local_cargo_demand_score'],
        'tourism_score' => (int)$row['tourism_score'],
        'business_score' => (int)$row['business_score'],
        'competition_score' => (int)$row['competition_score'],
        'airport_fee_score' => (int)$row['airport_fee_score'],
        'starting_difficulty' => $row['starting_difficulty'],
        'starting_base_note' => $row['starting_base_note'],
    ],
]);
