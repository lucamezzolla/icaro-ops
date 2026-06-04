<?php
declare(strict_types=1);

require __DIR__ . '/../../lib/bootstrap.php';

/*
 * Temporary development endpoint.
 *
 * For now we load by companyId from query string because full authentication/session
 * is not implemented yet. Later this must be replaced by the logged-in session.
 */

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

      v.world_region_code,
      v.world_region_name,
      v.country_id,
      v.country_name,
      v.icao_code,
      v.iata_code,
      v.airport_name,
      v.city,
      v.location_name,
      v.subdivision_name,
      v.latitude,
      v.longitude,
      v.airport_type,
      v.service_category,
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
      v.starting_base_note
    FROM companies co
    JOIN v_starting_base_airports v
      ON v.icao_code = co.base_airport_icao_code
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
