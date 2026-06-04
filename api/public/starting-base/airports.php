<?php
declare(strict_types=1);

require __DIR__ . '/../../lib/bootstrap.php';

$countryId = filter_input(INPUT_GET, 'countryId', FILTER_VALIDATE_INT);

if (!$countryId) {
    json_response(['error' => 'INVALID_COUNTRY_ID'], 422);
}

$stmt = db()->prepare("
    SELECT
      world_region_code,
      world_region_name,
      country_id,
      country_name,
      icao_code,
      iata_code,
      airport_name,
      city,
      location_name,
      subdivision_name,
      latitude,
      longitude,
      airport_type,
      service_category,
      base_tier,
      max_initial_aircraft_class,
      starting_base_score,
      local_passenger_demand_score,
      local_cargo_demand_score,
      tourism_score,
      business_score,
      competition_score,
      airport_fee_score,
      starting_difficulty,
      starting_base_note
    FROM v_starting_base_airports
    WHERE country_id = :country_id
    ORDER BY starting_base_score DESC, airport_name
");

$stmt->execute(['country_id' => $countryId]);

json_response($stmt->fetchAll());
