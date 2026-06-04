<?php
declare(strict_types=1);

require __DIR__ . '/../../lib/bootstrap.php';

/*
 * Temporary public rival-base endpoint.
 *
 * It returns limited public info only. Later this should respect visibility,
 * fog-of-war, discovered markets, authentication and rate limits.
 */

$companyId = filter_input(INPUT_GET, 'companyId', FILTER_VALIDATE_INT);

if (!$companyId) {
    json_response(['error' => 'INVALID_COMPANY_ID'], 422);
}

$stmt = db()->prepare("
    SELECT
      co.id AS company_id,
      co.company_name,
      co.reputation_score,

      v.country_name,
      v.icao_code,
      v.iata_code,
      v.airport_name,
      v.city,
      v.location_name,
      v.latitude,
      v.longitude,
      v.starting_difficulty
    FROM companies co
    JOIN v_starting_base_airports v
      ON v.icao_code = co.base_airport_icao_code
    WHERE co.id <> :company_id
    ORDER BY co.reputation_score DESC, co.company_name
    LIMIT 50
");

$stmt->execute(['company_id' => $companyId]);

$rows = array_map(static function (array $row): array {
    return [
        'company_id' => (int)$row['company_id'],
        'company_name' => $row['company_name'],
        'reputation_score' => (int)$row['reputation_score'],
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
}, $stmt->fetchAll());

json_response($rows);
