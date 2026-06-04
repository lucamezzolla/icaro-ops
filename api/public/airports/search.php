<?php
declare(strict_types=1);

require __DIR__ . '/../../lib/bootstrap.php';

$query = trim((string)($_GET['q'] ?? ''));

if (mb_strlen($query) < 2) {
    json_response([]);
}

$exact = strtoupper($query);
$like = '%' . $query . '%';
$prefixLike = $query . '%';

function airport_row(array $row): array
{
    return [
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
        'is_closed' => (bool)$row['is_closed'],
        'is_civilian' => (bool)$row['is_civilian'],
        'is_military' => (bool)$row['is_military'],
    ];
}

$baseSelect = "
    SELECT
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
      a.is_closed,
      a.is_civilian,
      a.is_military
    FROM airports a
    JOIN countries c
      ON c.id = a.country_id
    JOIN world_regions wr
      ON wr.code = c.world_region_code
";

/*
 * Exact ICAO/IATA search is handled first and returns only exact airport-code matches.
 * This prevents "LIRA" from returning fuzzy matches such as "Lira, Uganda".
 */
if (preg_match('/^[A-Z0-9]{3,4}$/', $exact) === 1) {
    $stmt = db()->prepare($baseSelect . "
        WHERE a.icao_code = :exact_icao
           OR a.iata_code = :exact_iata
        ORDER BY
          CASE
            WHEN a.icao_code = :order_exact_icao THEN 0
            WHEN a.iata_code = :order_exact_iata THEN 1
            ELSE 2
          END,
          a.name
        LIMIT 20
    ");

    $stmt->execute([
        'exact_icao' => $exact,
        'exact_iata' => $exact,
        'order_exact_icao' => $exact,
        'order_exact_iata' => $exact,
    ]);

    $rows = $stmt->fetchAll();

    if ($rows) {
        json_response(array_map('airport_row', $rows));
    }
}

$stmt = db()->prepare($baseSelect . "
    WHERE
      a.name LIKE :like_name
      OR a.city LIKE :like_city
      OR a.location_name LIKE :like_location
      OR a.subdivision_name LIKE :like_subdivision
      OR c.name LIKE :like_country
    ORDER BY
      CASE
        WHEN a.name LIKE :prefix_name THEN 0
        WHEN a.city LIKE :prefix_city THEN 1
        WHEN a.location_name LIKE :prefix_location THEN 2
        ELSE 3
      END,
      CASE WHEN a.latitude IS NULL OR a.longitude IS NULL THEN 1 ELSE 0 END,
      a.name
    LIMIT 20
");

$stmt->execute([
    'like_name' => $like,
    'like_city' => $like,
    'like_location' => $like,
    'like_subdivision' => $like,
    'like_country' => $like,
    'prefix_name' => $prefixLike,
    'prefix_city' => $prefixLike,
    'prefix_location' => $prefixLike,
]);

json_response(array_map('airport_row', $stmt->fetchAll()));
