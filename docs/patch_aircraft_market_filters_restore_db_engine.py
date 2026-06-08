#!/usr/bin/env python3
from pathlib import Path
import re

ROOT = Path.cwd()
CATALOG = ROOT / "api/public/fleet/catalog.php"
DIALOG = ROOT / "src/js/fleet-market-table-dialog.js"
FILTERS = ROOT / "src/js/aircraft-market-filters.js"


def backup(path: Path) -> None:
    b = path.with_suffix(path.suffix + ".before_restore_engine_filters")
    if not b.exists():
        b.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")


def patch_catalog() -> None:
    if not CATALOG.exists():
        raise SystemExit(f"Missing {CATALOG}")
    backup(CATALOG)
    CATALOG.write_text(r'''<?php
declare(strict_types=1);

require __DIR__ . '/../../lib/bootstrap.php';
require __DIR__ . '/../../lib/session.php';

$session = require_auth_session();
$companyId = (int)$session['company_id'];
$pdo = db();

$companyStmt = $pdo->prepare("
    SELECT
      currency_code,
      base_airport_icao_code,
      budget_amount
    FROM companies
    WHERE id = :company_id
    LIMIT 1
");
$companyStmt->execute(['company_id' => $companyId]);
$company = $companyStmt->fetch() ?: [
    'currency_code' => 'EUR',
    'base_airport_icao_code' => null,
    'budget_amount' => 0,
];

$priceColumn = first_existing_column($pdo, 'aircraft_models', [
    'new_purchase_price',
    'base_purchase_price',
    'new_price',
    'purchase_price',
    'estimated_new_price',
    'catalog_price',
    'price_amount',
    'new_cost_amount'
]);

if ($priceColumn === null) {
    json_response([
        'error' => 'AIRCRAFT_PRICE_COLUMN_NOT_FOUND',
        'message' => 'No supported aircraft price column was found in aircraft_models.',
    ], 500);
}

$engineTypeColumn = first_existing_column($pdo, 'aircraft_models', [
    'engine_type'
]);
$engineTypeExpr = $engineTypeColumn !== null ? "COALESCE({$engineTypeColumn}, '')" : "''";

/*
 * Development/open market:
 * show every aircraft model. Purchase blocking is budget-only.
 */
$sql = "
    SELECT
      id AS aircraft_model_id,
      id,
      manufacturer,
      model_name,
      model_code,
      icao_type_code,
      {$engineTypeExpr} AS engine_type,
      operation_role,
      passenger_capacity_standard,
      range_km,
      cruise_speed_kmh,
      fuel_burn_kg_per_hour,
      maintenance_cost_per_hour,
      image_asset_path,
      COALESCE({$priceColumn}, 0) AS new_purchase_price,
      COALESCE(currency_code, :currency_code) AS currency_code,
      is_active,
      is_available_new,
      is_endgame,
      unlock_reputation_score
    FROM aircraft_models
    ORDER BY
      COALESCE({$priceColumn}, 0),
      manufacturer,
      model_name
";

$stmt = $pdo->prepare($sql);
$stmt->execute(['currency_code' => $company['currency_code'] ?? 'EUR']);

$aircraft = [];
$budget = (float)($company['budget_amount'] ?? 0);

foreach ($stmt->fetchAll() as $row) {
    $price = (float)($row['new_purchase_price'] ?? 0);

    $row['engine_type'] = strtoupper(trim((string)($row['engine_type'] ?? '')));
    $row['currency_code'] = $row['currency_code'] ?: ($company['currency_code'] ?? 'EUR');
    $row['purchase_rule'] = 'BUDGET_ONLY';
    $row['budget_amount'] = number_format($budget, 2, '.', '');
    $row['can_afford'] = $budget >= $price;

    /* Compatibility fields kept for the current UI, but they no longer block purchase. */
    $row['current_qualified_pilots'] = null;
    $row['required_pilots_after_purchase'] = null;
    $row['pilot_coverage_ok_after_purchase'] = true;
    $row['required_license'] = null;
    $row['unlock_status'] = 'AVAILABLE_FOR_DEVELOPMENT_TEST';
    $row['unlock_note'] = 'Development mode: all aircraft are visible. Purchase is limited only by budget.';

    $aircraft[] = $row;
}

json_response([
    'level' => [
        'base_airport_icao_code' => $company['base_airport_icao_code'] ?? null,
        'base_tier' => 'DEVELOPMENT_OPEN_MARKET',
        'airport_size_tier' => null,
        'max_initial_aircraft_class' => 'ANY',
        'rule' => 'Development mode: all aircraft are visible. Purchase is budget-only.',
    ],
    'purchase_rule' => [
        'mode' => 'BUDGET_ONLY',
        'budget_amount' => number_format($budget, 2, '.', ''),
        'currency_code' => $company['currency_code'] ?? 'EUR',
        'rule' => 'Only the company budget can block aircraft purchase.',
    ],
    'pilot_coverage' => [
        'current_qualified_pilots' => null,
        'required_pilots_for_current_fleet' => null,
        'required_pilots_after_purchase' => null,
        'rule' => 'Disabled in development open-market mode.',
    ],
    'aircraft' => $aircraft,
]);

function first_existing_column(PDO $pdo, string $tableName, array $candidates): ?string
{
    $stmt = $pdo->prepare("
        SELECT COLUMN_NAME
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = :table_name
    ");
    $stmt->execute(['table_name' => $tableName]);

    $columns = array_flip(array_map(static fn ($row) => $row['COLUMN_NAME'], $stmt->fetchAll()));

    foreach ($candidates as $candidate) {
        if (isset($columns[$candidate])) {
            return '`' . str_replace('`', '``', $candidate) . '`';
        }
    }

    return null;
}
''', encoding="utf-8")


def patch_dialog() -> None:
    if not DIALOG.exists():
        raise SystemExit(f"Missing {DIALOG}")
    backup(DIALOG)
    text = DIALOG.read_text(encoding="utf-8")

    # Add stable data attributes to the aircraft market table rows.
    text = re.sub(
        r'<tr\s+(?:data-aircraft-icao="\$\{escapeHtml\(row\.icao_type_code \|\| ""\)\}"\s+data-engine-type="\$\{escapeHtml\(row\.engine_type \|\| ""\)\}"\s+data-price="\$\{escapeHtml\(String\(row\.new_purchase_price \?\? ""\)\)\}"\s+data-pax="\$\{escapeHtml\(String\(row\.passenger_capacity_standard \?\? ""\)\)\}")?>',
        '<tr>',
        text,
    )

    old = """${aircraft.map(row => `\n            <tr>"""
    new = """${aircraft.map(row => `\n            <tr\n              data-aircraft-icao="${escapeHtml(row.icao_type_code || row.model_code || "")}"\n              data-engine-type="${escapeHtml(row.engine_type || "")}"\n              data-price="${escapeHtml(String(row.new_purchase_price ?? ""))}"\n              data-pax="${escapeHtml(String(row.passenger_capacity_standard ?? ""))}"\n            >"""
    if old in text:
        text = text.replace(old, new, 1)
    elif 'data-engine-type=' not in text:
        raise SystemExit("Could not find aircraft row template in src/js/fleet-market-table-dialog.js")

    DIALOG.write_text(text, encoding="utf-8")


def patch_filters() -> None:
    FILTERS.parent.mkdir(parents=True, exist_ok=True)
    if FILTERS.exists():
        backup(FILTERS)
    FILTERS.write_text(r'''(() => {
  const DIALOG_SELECTOR = "#aircraftMarketTableDialog";
  const BODY_SELECTOR = "#aircraftMarketTableBody";
  const FILTER_ID = "aircraftMarketFilters";

  document.addEventListener("DOMContentLoaded", () => {
    const observer = new MutationObserver(() => {
      ensureAircraftMarketFilters();
      applyAircraftMarketFilters();
    });

    observer.observe(document.body, {
      childList: true,
      subtree: true
    });

    ensureAircraftMarketFilters();
  });

  function ensureAircraftMarketFilters() {
    const dialog = document.querySelector(DIALOG_SELECTOR);
    const body = document.querySelector(BODY_SELECTOR);

    if (!dialog || !body || !body.querySelector("table")) {
      return;
    }

    if (dialog.querySelector(`#${FILTER_ID}`)) {
      return;
    }

    const filters = document.createElement("section");
    filters.id = FILTER_ID;
    filters.className = "aircraft-market-filters";
    filters.innerHTML = `
      <div class="aircraft-market-filter-grid">
        <label>
          <span>ICAO</span>
          <input type="search" id="aircraftFilterIcao" autocomplete="off" placeholder="B738, A320, CONC">
        </label>

        <label>
          <span>Search</span>
          <input type="search" id="aircraftFilterText" autocomplete="off" placeholder="Boeing, Airbus, Concorde">
        </label>

        <label>
          <span>Max price</span>
          <input type="number" id="aircraftFilterMaxPrice" min="0" step="100000">
        </label>

        <label>
          <span>Min pax</span>
          <input type="number" id="aircraftFilterMinPax" min="0" step="1">
        </label>

        <label>
          <span>Max pax</span>
          <input type="number" id="aircraftFilterMaxPax" min="0" step="1">
        </label>

        <label>
          <span>Engine</span>
          <select id="aircraftFilterEngine">
            <option value="">All engines</option>
            <option value="TURBOFAN">Turbofan / jet</option>
            <option value="TURBOPROP">Turboprop</option>
            <option value="PISTON">Piston</option>
            <option value="TURBOSHAFT">Turboshaft / helicopter</option>
            <option value="SUPERSONIC">Supersonic</option>
          </select>
        </label>

        <button type="button" id="aircraftFilterClear" class="secondary">Clear</button>
      </div>
    `;

    body.parentNode.insertBefore(filters, body);

    filters.querySelectorAll("input, select").forEach(input => {
      input.addEventListener("input", applyAircraftMarketFilters);
      input.addEventListener("change", applyAircraftMarketFilters);
    });

    filters.querySelector("#aircraftFilterClear").addEventListener("click", () => {
      filters.querySelectorAll("input").forEach(input => input.value = "");
      filters.querySelectorAll("select").forEach(select => select.value = "");
      applyAircraftMarketFilters();
    });
  }

  function applyAircraftMarketFilters() {
    const dialog = document.querySelector(DIALOG_SELECTOR);
    const filters = dialog?.querySelector(`#${FILTER_ID}`);
    const rows = Array.from(dialog?.querySelectorAll(`${BODY_SELECTOR} tbody tr`) || []);

    if (!dialog || !filters || rows.length === 0) {
      return;
    }

    const criteria = readCriteria(filters);

    rows.forEach(row => {
      const data = readRowData(row);
      const visible = matchesCriteria(data, criteria);
      row.hidden = !visible;
      row.classList.toggle("aircraft-market-filter-hidden", !visible);
    });
  }

  function readCriteria(filters) {
    return {
      icao: getValue(filters, "#aircraftFilterIcao").toUpperCase(),
      text: getValue(filters, "#aircraftFilterText").toLowerCase(),
      maxPrice: toNumberOrNull(getValue(filters, "#aircraftFilterMaxPrice")),
      minPax: toNumberOrNull(getValue(filters, "#aircraftFilterMinPax")),
      maxPax: toNumberOrNull(getValue(filters, "#aircraftFilterMaxPax")),
      engine: getValue(filters, "#aircraftFilterEngine").toUpperCase()
    };
  }

  function readRowData(row) {
    const text = normalize(row.textContent);
    const cells = row.querySelectorAll("td");

    return {
      text,
      lowerText: text.toLowerCase(),
      icao: normalize(row.dataset.aircraftIcao || cells[0]?.textContent || "").toUpperCase(),
      engine: normalize(row.dataset.engineType || row.dataset.aircraftEngine || "").toUpperCase(),
      price: toNumberOrNull(row.dataset.price || cells[4]?.textContent || ""),
      pax: toNumberOrNull(row.dataset.pax || cells[2]?.textContent || "")
    };
  }

  function matchesCriteria(data, criteria) {
    if (criteria.icao && !data.icao.includes(criteria.icao)) {
      return false;
    }

    if (criteria.text && !data.lowerText.includes(criteria.text)) {
      return false;
    }

    if (criteria.engine && data.engine !== criteria.engine) {
      return false;
    }

    if (criteria.maxPrice !== null && (data.price === null || data.price > criteria.maxPrice)) {
      return false;
    }

    if (criteria.minPax !== null && (data.pax === null || data.pax < criteria.minPax)) {
      return false;
    }

    if (criteria.maxPax !== null && (data.pax === null || data.pax > criteria.maxPax)) {
      return false;
    }

    return true;
  }

  function getValue(root, selector) {
    return String(root.querySelector(selector)?.value || "").trim();
  }

  function normalize(value) {
    return String(value || "").replace(/\s+/g, " ").trim();
  }

  function toNumberOrNull(value) {
    const normalized = String(value || "")
      .replace(/[^0-9.,-]/g, "")
      .replace(/,/g, "");

    if (!normalized) {
      return null;
    }

    const parsed = Number(normalized);
    return Number.isFinite(parsed) ? parsed : null;
  }
})();
''', encoding="utf-8")


patch_catalog()
patch_dialog()
patch_filters()
print("Patched aircraft market filters with exact DB engine_type values.")
