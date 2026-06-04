<?php
declare(strict_types=1);

require __DIR__ . '/../../lib/bootstrap.php';

/*
 * Public map bases endpoint.
 *
 * Returns limited visible base data for:
 * - physical player companies
 * - virtual rival companies
 *
 * Later this endpoint should respect authentication, fog-of-war and visibility rules.
 */

$rows = [];

$companyStmt = db()->query("
    SELECT
      'PLAYER' AS base_owner_type,
      co.id AS company_id,
      co.company_name,
      co.reputation_score,
      co.currency_code,
      co.budget_amount,
      CONCAT_WS(' ', NULLIF(p.first_name, ''), NULLIF(p.last_name, '')) AS owner_name,
      NULL AS strategy_type,

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

      COALESCE(v.base_tier, 'UNCLASSIFIED') AS base_tier,
      COALESCE(v.local_passenger_demand_score, 0) AS local_passenger_demand_score,
      COALESCE(v.local_cargo_demand_score, 0) AS local_cargo_demand_score,
      COALESCE(v.tourism_score, 0) AS tourism_score,
      COALESCE(v.business_score, 0) AS business_score,
      COALESCE(v.competition_score, 0) AS competition_score,
      COALESCE(v.airport_fee_score, 0) AS airport_fee_score,
      COALESCE(v.starting_difficulty, 'UNKNOWN') AS starting_difficulty,

      COALESCE(acp.airport_size_tier, 'UNCLASSIFIED') AS airport_size_tier,
      COALESCE(acp.max_total_bases, 1) AS max_total_bases
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
    WHERE a.latitude IS NOT NULL
      AND a.longitude IS NOT NULL
");

foreach ($companyStmt->fetchAll() as $row) {
    $rows[] = $row;
}

$rivalStmt = db()->query("
    SELECT
      'RIVAL' AS base_owner_type,
      rc.id AS company_id,
      rc.company_name,
      rc.reputation_score,
      NULL AS currency_code,
      NULL AS budget_amount,
      'Virtual rival' AS owner_name,
      rc.strategy_type,

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

      COALESCE(v.base_tier, 'UNCLASSIFIED') AS base_tier,
      COALESCE(v.local_passenger_demand_score, 0) AS local_passenger_demand_score,
      COALESCE(v.local_cargo_demand_score, 0) AS local_cargo_demand_score,
      COALESCE(v.tourism_score, 0) AS tourism_score,
      COALESCE(v.business_score, 0) AS business_score,
      COALESCE(v.competition_score, 0) AS competition_score,
      COALESCE(v.airport_fee_score, 0) AS airport_fee_score,
      COALESCE(v.starting_difficulty, 'UNKNOWN') AS starting_difficulty,

      COALESCE(acp.airport_size_tier, 'UNCLASSIFIED') AS airport_size_tier,
      COALESCE(acp.max_total_bases, 1) AS max_total_bases
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
    LEFT JOIN airport_capacity_profiles acp
      ON acp.airport_icao_code = a.icao_code
    WHERE rc.is_active = TRUE
      AND a.latitude IS NOT NULL
      AND a.longitude IS NOT NULL
");

foreach ($rivalStmt->fetchAll() as $row) {
    $rows[] = $row;
}

json_response(array_map(static function (array $row): array {
    return [
        'base_owner_type' => $row['base_owner_type'],
        'company_id' => (int)$row['company_id'],
        'company_name' => $row['company_name'],
        'owner_name' => trim((string)($row['owner_name'] ?? '')) ?: 'Unknown',
        'reputation_score' => (int)$row['reputation_score'],
        'currency_code' => $row['currency_code'],
        'budget_amount' => $row['budget_amount'],
        'strategy_type' => $row['strategy_type'],

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
        'local_passenger_demand_score' => (int)$row['local_passenger_demand_score'],
        'local_cargo_demand_score' => (int)$row['local_cargo_demand_score'],
        'tourism_score' => (int)$row['tourism_score'],
        'business_score' => (int)$row['business_score'],
        'competition_score' => (int)$row['competition_score'],
        'airport_fee_score' => (int)$row['airport_fee_score'],
        'starting_difficulty' => $row['starting_difficulty'],

        'airport_size_tier' => $row['airport_size_tier'],
        'max_total_bases' => (int)$row['max_total_bases'],
    ];
}, $rows));
