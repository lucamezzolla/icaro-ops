<?php
declare(strict_types=1);

require __DIR__ . '/../../lib/bootstrap.php';

$companyId = filter_input(INPUT_GET, 'companyId', FILTER_VALIDATE_INT);

if (!$companyId) {
    json_response(['error' => 'INVALID_COMPANY_ID'], 422);
}

$stmt = db()->prepare("
    SELECT
      rb.id AS rival_base_id,
      rc.id AS rival_company_id,
      rc.company_name,
      rc.reputation_score,
      rc.strategy_type,

      wr.name AS world_region_name,
      c.name AS country_name,
      a.icao_code,
      a.iata_code,
      a.name AS airport_name,
      a.city,
      a.location_name,
      a.latitude,
      a.longitude,
      COALESCE(v.starting_difficulty, 'UNKNOWN') AS starting_difficulty
    FROM rival_company_bases rb
    JOIN rival_companies rc
      ON rc.id = rb.rival_company_id
    JOIN airports a
      ON a.icao_code = rb.airport_icao_code
    JOIN countries c
      ON c.id = a.country_id
    JOIN world_regions wr
      ON wr.code = c.world_region_code
    LEFT JOIN v_starting_base_airports v
      ON v.icao_code = a.icao_code
    WHERE rc.is_active = TRUE
    ORDER BY rc.reputation_score DESC, rc.company_name
    LIMIT 100
");

$stmt->execute();

json_response(array_map(static function (array $row): array {
    return [
        'rival_base_id' => (int)$row['rival_base_id'],
        'rival_company_id' => (int)$row['rival_company_id'],
        'company_name' => $row['company_name'],
        'reputation_score' => (int)$row['reputation_score'],
        'strategy_type' => $row['strategy_type'],
        'world_region_name' => $row['world_region_name'],
        'country_name' => $row['country_name'],
        'icao_code' => $row['icao_code'],
        'iata_code' => $row['iata_code'],
        'airport_name' => $row['airport_name'],
        'city' => $row['city'],
        'location_name' => $row['location_name'],
        'latitude' => $row['latitude'],
        'longitude' => $row['longitude'],
        'starting_difficulty' => $row['starting_difficulty'],
    ];
}, $stmt->fetchAll()));
