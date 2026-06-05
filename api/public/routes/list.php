<?php
declare(strict_types=1);

require __DIR__ . '/../../lib/bootstrap.php';
require __DIR__ . '/../../lib/session.php';

$session = require_auth_session();
$companyId = (int)$session['company_id'];

$pdo = db();

/*
 * Routes page now lists scheduled services over abstract air_routes.
 * A service is NOT a flight. Flights are generated/started later.
 */
$stmt = $pdo->prepare("
    SELECT
      ss.id AS service_id,
      ss.id AS route_id,
      ss.service_code,
      ss.company_id,
      ss.air_route_id,
      ss.recurrence_type,
      ss.scheduled_departure_time_utc,
      ss.service_status AS status,
      ss.required_aircraft_class,
      ss.preferred_aircraft_model_id,
      ss.base_ticket_price AS ticket_price,
      ss.currency_code,
      ss.auto_dispatch_enabled,
      ss.allow_backup_aircraft,
      ss.allow_extra_flights,

      ar.route_code,
      ar.origin_airport_icao_code,
      ar.destination_airport_icao_code,
      ar.route_scope,
      ar.route_market,
      ar.route_operation_domain,
      ar.planned_distance_km,
      ar.estimated_block_minutes AS planned_duration_minutes,

      oa.name AS origin_airport_name,
      da.name AS destination_airport_name,

      am.manufacturer,
      am.model_name,
      am.model_code,
      am.icao_type_code,

      (
        SELECT COUNT(*)
        FROM scheduled_flight_instances f
        WHERE f.company_id = ss.company_id
          AND f.scheduled_service_id = ss.id
      ) AS generated_flights_count,

      (
        SELECT COUNT(*)
        FROM scheduled_flight_instances f
        WHERE f.company_id = ss.company_id
          AND f.scheduled_service_id = ss.id
          AND f.status = 'IN_FLIGHT'
      ) AS active_flights_count
    FROM scheduled_services ss
    JOIN air_routes ar
      ON ar.id = ss.air_route_id
    LEFT JOIN airports oa
      ON oa.icao_code = ar.origin_airport_icao_code
    LEFT JOIN airports da
      ON da.icao_code = ar.destination_airport_icao_code
    LEFT JOIN aircraft_models am
      ON am.id = ss.preferred_aircraft_model_id
    WHERE ss.company_id = :company_id
    ORDER BY ss.scheduled_departure_time_utc, ar.origin_airport_icao_code, ar.destination_airport_icao_code
");
$stmt->execute(['company_id' => $companyId]);

json_response($stmt->fetchAll());
