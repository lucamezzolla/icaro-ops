<?php
declare(strict_types=1);

require __DIR__ . '/../../lib/bootstrap.php';
require __DIR__ . '/../../lib/session.php';

require_auth_session();

$q = strtoupper(trim((string)($_GET['q'] ?? '')));
$limit = max(5, min(50, (int)($_GET['limit'] ?? 25)));

$pdo = db();

if ($q === '') {
    $stmt = $pdo->prepare("
        SELECT icao_code, iata_code, name, city, country_id, latitude, longitude, airport_size_tier
        FROM airports
        WHERE latitude IS NOT NULL
          AND longitude IS NOT NULL
        ORDER BY icao_code
        LIMIT :limit
    ");
    $stmt->bindValue(':limit', $limit, PDO::PARAM_INT);
    $stmt->execute();
    json_response(['airports' => $stmt->fetchAll()]);
}

$stmt = $pdo->prepare("
    SELECT icao_code, iata_code, name, city, country_id, latitude, longitude, airport_size_tier
    FROM airports
    WHERE latitude IS NOT NULL
      AND longitude IS NOT NULL
      AND (
        icao_code LIKE :prefix
        OR iata_code LIKE :prefix
        OR UPPER(name) LIKE :contains
        OR UPPER(city) LIKE :contains
      )
    ORDER BY
      CASE
        WHEN icao_code = :exact THEN 1
        WHEN iata_code = :exact THEN 2
        WHEN icao_code LIKE :prefix THEN 3
        ELSE 4
      END,
      icao_code
    LIMIT :limit
");
$stmt->bindValue(':exact', $q);
$stmt->bindValue(':prefix', $q . '%');
$stmt->bindValue(':contains', '%' . $q . '%');
$stmt->bindValue(':limit', $limit, PDO::PARAM_INT);
$stmt->execute();

json_response(['airports' => $stmt->fetchAll()]);
