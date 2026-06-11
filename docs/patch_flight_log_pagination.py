#!/usr/bin/env python3
from pathlib import Path

PROJECT = Path.cwd()
FLIGHT_LOG_HTML = PROJECT / "flight-log.html"
FLIGHT_LOG_JS = PROJECT / "src/js/flight-log.js"
FLIGHT_LOG_PHP = PROJECT / "api/public/flights/log.php"
FLIGHT_LOG_CSS = PROJECT / "src/css/flight-log.css"

LOG_PHP_CONTENT = r'''<?php
declare(strict_types=1);

require __DIR__ . '/../../lib/bootstrap.php';
require __DIR__ . '/../../lib/session.php';

$session = require_auth_session();
$companyId = (int)$session['company_id'];
$pdo = db();

$pageSize = 10;
$page = filter_input(INPUT_GET, 'page', FILTER_VALIDATE_INT);

if (!$page || $page < 1) {
    $page = 1;
}

$totalStmt = $pdo->prepare("
    SELECT COUNT(*)
    FROM scheduled_flight_instances
    WHERE company_id = :company_id
");
$totalStmt->execute(['company_id' => $companyId]);
$totalFlights = (int)$totalStmt->fetchColumn();

$totalPages = max(1, (int)ceil($totalFlights / $pageSize));

if ($page > $totalPages) {
    $page = $totalPages;
}

$offset = ($page - 1) * $pageSize;

$stmt = $pdo->prepare("
    SELECT
      f.id AS flight_id, f.route_id, f.company_id, f.aircraft_id, f.flight_code, f.flight_date_utc,
      f.origin_airport_icao_code, f.destination_airport_icao_code,
      f.scheduled_departure_at_utc, f.scheduled_arrival_at_utc,
      f.actual_departure_at_utc, f.actual_arrival_at_utc,
      f.status, f.passenger_capacity, f.passenger_count, f.load_factor_percent,
      f.ticket_price, f.passenger_revenue, f.fuel_cost, f.maintenance_cost,
      f.staff_cost, f.total_operating_cost, f.profit_amount, f.currency_code,
      ca.registration_code, am.manufacturer, am.model_name, am.model_code, am.icao_type_code
    FROM scheduled_flight_instances f
    LEFT JOIN company_aircraft ca ON ca.id = f.aircraft_id
    LEFT JOIN aircraft_models am ON am.id = ca.aircraft_model_id
    WHERE f.company_id = :company_id
    ORDER BY COALESCE(f.actual_departure_at_utc, f.scheduled_departure_at_utc) DESC, f.id DESC
    LIMIT :limit_rows OFFSET :offset_rows
");
$stmt->bindValue(':company_id', $companyId, PDO::PARAM_INT);
$stmt->bindValue(':limit_rows', $pageSize, PDO::PARAM_INT);
$stmt->bindValue(':offset_rows', $offset, PDO::PARAM_INT);
$stmt->execute();
$flights = $stmt->fetchAll();

$summaryStmt = $pdo->prepare("
    SELECT
      COUNT(*) AS total_flights,
      SUM(CASE WHEN status = 'COMPLETED' THEN 1 ELSE 0 END) AS completed_flights,
      SUM(CASE WHEN status = 'IN_FLIGHT' THEN 1 ELSE 0 END) AS in_flight_count,
      COALESCE(SUM(profit_amount), 0) AS total_profit_amount,
      MAX(currency_code) AS currency_code
    FROM scheduled_flight_instances
    WHERE company_id = :company_id
");
$summaryStmt->execute(['company_id' => $companyId]);
$summary = $summaryStmt->fetch() ?: [];

json_response([
    'summary' => [
        'total_flights' => (int)($summary['total_flights'] ?? 0),
        'completed_flights' => (int)($summary['completed_flights'] ?? 0),
        'in_flight_count' => (int)($summary['in_flight_count'] ?? 0),
        'total_profit_amount' => $summary['total_profit_amount'] ?? '0.00',
        'currency_code' => $summary['currency_code'] ?: 'EUR',
    ],
    'pagination' => [
        'page' => $page,
        'page_size' => $pageSize,
        'total_records' => $totalFlights,
        'total_pages' => $totalPages,
        'has_previous' => $page > 1,
        'has_next' => $page < $totalPages,
    ],
    'flights' => array_map(static function (array $row): array {
        return [
            'flight_id' => (int)$row['flight_id'],
            'route_id' => (int)$row['route_id'],
            'aircraft_id' => (int)$row['aircraft_id'],
            'flight_code' => $row['flight_code'],
            'flight_date_utc' => $row['flight_date_utc'],
            'origin_airport_icao_code' => $row['origin_airport_icao_code'],
            'destination_airport_icao_code' => $row['destination_airport_icao_code'],
            'scheduled_departure_at_utc' => $row['scheduled_departure_at_utc'],
            'scheduled_arrival_at_utc' => $row['scheduled_arrival_at_utc'],
            'actual_departure_at_utc' => $row['actual_departure_at_utc'],
            'actual_arrival_at_utc' => $row['actual_arrival_at_utc'],
            'status' => $row['status'],
            'passenger_capacity' => (int)$row['passenger_capacity'],
            'passenger_count' => (int)$row['passenger_count'],
            'load_factor_percent' => (int)$row['load_factor_percent'],
            'ticket_price' => $row['ticket_price'],
            'passenger_revenue' => $row['passenger_revenue'],
            'fuel_cost' => $row['fuel_cost'],
            'maintenance_cost' => $row['maintenance_cost'],
            'staff_cost' => $row['staff_cost'],
            'total_operating_cost' => $row['total_operating_cost'],
            'profit_amount' => $row['profit_amount'],
            'currency_code' => $row['currency_code'],
            'registration_code' => $row['registration_code'],
            'manufacturer' => $row['manufacturer'],
            'model_name' => $row['model_name'],
            'model_code' => $row['model_code'],
            'icao_type_code' => $row['icao_type_code'],
        ];
    }, $flights),
]);
'''

CSS_APPEND = r'''
.flight-log-pagination {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin: 12px 0;
  padding: 10px 12px;
  border: 1px solid rgba(255,255,255,.10);
  border-radius: 14px;
  background: rgba(255,255,255,.04);
}

.flight-log-pagination .pagination-info {
  color: var(--muted);
  font-weight: 700;
}

.flight-log-pagination .pagination-buttons {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.flight-log-pagination button[disabled] {
  opacity: .45;
  cursor: not-allowed;
}

@media(max-width:720px) {
  .flight-log-pagination {
    align-items: stretch;
    flex-direction: column;
  }

  .flight-log-pagination .pagination-buttons {
    justify-content: flex-start;
  }
}
'''

PAGINATION_HELPERS = r'''
function renderPaginationControls() {
  const top = document.querySelector("#flightLogPaginationTop");
  const bottom = document.querySelector("#flightLogPaginationBottom");

  if (!top && !bottom) {
    return;
  }

  const html = paginationControlsHtml();

  [top, bottom].forEach(container => {
    if (!container) {
      return;
    }

    container.innerHTML = html;

    container.querySelectorAll("[data-flight-log-page]").forEach(button => {
      button.addEventListener("click", () => {
        const page = Number(button.dataset.flightLogPage || 1);
        loadFlightLog(page);
      });
    });
  });
}

function paginationControlsHtml() {
  const page = Number(currentFlightLogPagination.page || 1);
  const pageSize = Number(currentFlightLogPagination.page_size || FLIGHT_LOG_PAGE_SIZE);
  const totalRecords = Number(currentFlightLogPagination.total_records || 0);
  const totalPages = Math.max(1, Number(currentFlightLogPagination.total_pages || 1));
  const firstRecord = totalRecords === 0 ? 0 : ((page - 1) * pageSize) + 1;
  const lastRecord = Math.min(totalRecords, page * pageSize);

  return `
    <div class="pagination-info">
      Page ${page} of ${totalPages} - Records ${firstRecord}-${lastRecord} of ${totalRecords}
    </div>
    <div class="pagination-buttons">
      <button type="button" data-flight-log-page="1" ${page <= 1 ? "disabled" : ""}>First</button>
      <button type="button" data-flight-log-page="${Math.max(1, page - 1)}" ${page <= 1 ? "disabled" : ""}>Previous</button>
      <button type="button" data-flight-log-page="${Math.min(totalPages, page + 1)}" ${page >= totalPages ? "disabled" : ""}>Next</button>
      <button type="button" data-flight-log-page="${totalPages}" ${page >= totalPages ? "disabled" : ""}>Last</button>
    </div>
  `;
}
'''

def read(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path}")
    return path.read_text(encoding="utf-8")

def write(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")

def patch_html() -> None:
    html = read(FLIGHT_LOG_HTML)

    if 'id="flightLogPaginationTop"' not in html:
        html = html.replace(
            '<div class="table-wrap">\n            <table>',
            '<div id="flightLogPaginationTop" class="flight-log-pagination"></div>\n\n          <div class="table-wrap">\n            <table>',
            1
        )

    if 'id="flightLogPaginationBottom"' not in html:
        html = html.replace(
            '</table>\n          </div>\n        </article>',
            '</table>\n          </div>\n\n          <div id="flightLogPaginationBottom" class="flight-log-pagination"></div>\n        </article>',
            1
        )

    write(FLIGHT_LOG_HTML, html)

def patch_js() -> None:
    js = read(FLIGHT_LOG_JS)

    old_api = '''const API = {
  list: "api/public/flights/log.php",
  detail: id => `api/public/flights/detail.php?flightId=${encodeURIComponent(id)}`
};'''
    new_api = '''const API = {
  list: page => `api/public/flights/log.php?page=${encodeURIComponent(page)}`,
  detail: id => `api/public/flights/detail.php?flightId=${encodeURIComponent(id)}`
};

const FLIGHT_LOG_PAGE_SIZE = 10;
let currentFlightLogPage = 1;
let currentFlightLogPagination = {
  page: 1,
  page_size: FLIGHT_LOG_PAGE_SIZE,
  total_records: 0,
  total_pages: 1,
  has_previous: false,
  has_next: false
};'''

    if "const FLIGHT_LOG_PAGE_SIZE" not in js:
        if old_api not in js:
            raise RuntimeError("Could not find API block in src/js/flight-log.js")
        js = js.replace(old_api, new_api, 1)

    js = js.replace(
        'document.querySelector("#refreshButton")?.addEventListener("click", loadFlightLog);\n  await loadFlightLog();',
        'document.querySelector("#refreshButton")?.addEventListener("click", () => loadFlightLog(currentFlightLogPage));\n  await loadFlightLog(1);',
        1
    )

    old_load = '''async function loadFlightLog() {
  hideError();
  try {
    const data = await getJson(API.list);
    renderSummary(data.summary || {});
    renderFlights(data.flights || []);
  } catch (error) {
    showError(error.message || "Unable to load flight log.");
  }
}'''
    new_load = '''async function loadFlightLog(page = 1) {
  hideError();
  try {
    const data = await getJson(API.list(page));
    currentFlightLogPagination = data.pagination || currentFlightLogPagination;
    currentFlightLogPage = Number(currentFlightLogPagination.page || page || 1);
    renderSummary(data.summary || {});
    renderFlights(data.flights || []);
    renderPaginationControls();
  } catch (error) {
    showError(error.message || "Unable to load flight log.");
  }
}'''

    if old_load in js:
        js = js.replace(old_load, new_load, 1)

    if "function renderPaginationControls(" not in js:
        marker = "function renderSummary(summary) {"
        if marker not in js:
            raise RuntimeError("Could not find renderSummary marker")
        js = js.replace(marker, PAGINATION_HELPERS + "\n" + marker, 1)

    write(FLIGHT_LOG_JS, js)

def patch_php() -> None:
    write(FLIGHT_LOG_PHP, LOG_PHP_CONTENT)

def patch_css() -> None:
    css = read(FLIGHT_LOG_CSS)
    if "flight-log-pagination" not in css:
        css = css.rstrip() + "\n\n" + CSS_APPEND.strip() + "\n"
    write(FLIGHT_LOG_CSS, css)

def main() -> None:
    patch_html()
    patch_js()
    patch_php()
    patch_css()
    print("Patched Flight Log pagination: 10 rows per page, newest first, controls above and below the table.")

if __name__ == "__main__":
    main()
