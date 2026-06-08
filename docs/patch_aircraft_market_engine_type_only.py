#!/usr/bin/env python3
from pathlib import Path
import re

ROOT = Path.cwd()
CATALOG = ROOT / 'api/public/fleet/catalog.php'
DIALOG = ROOT / 'src/js/fleet-market-table-dialog.js'
FILTERS = ROOT / 'src/js/aircraft-market-filters.js'
DOC = ROOT / 'docs/AIRCRAFT_MARKET_ENGINE_TYPE_ONLY.md'

for path in (CATALOG, DIALOG):
    if not path.exists():
        raise SystemExit(f'Missing file: {path}')

# 1) catalog.php: do not select removed columns; ensure engine_type is returned.
catalog = CATALOG.read_text()

# Remove SELECT lines for dropped columns.
catalog = re.sub(r'^[ \t]*aircraft_family,\s*\n', '', catalog, flags=re.MULTILINE)
catalog = re.sub(r'^[ \t]*aircraft_category,\s*\n', '', catalog, flags=re.MULTILINE)

select_prefix = catalog.split('FROM aircraft_models', 1)[0] if 'FROM aircraft_models' in catalog else catalog
if 'engine_type' not in select_prefix:
    anchors = [
        '      operation_role,\n',
        '    operation_role,\n',
        'operation_role,\n',
        '      iata_type_code,\n',
        '    iata_type_code,\n',
    ]
    inserted = False
    for anchor in anchors:
        if anchor in catalog:
            catalog = catalog.replace(anchor, anchor + '      engine_type,\n', 1)
            inserted = True
            break
    if not inserted:
        raise SystemExit('Could not safely add engine_type to catalog SELECT')

CATALOG.write_text(catalog)

# 2) fleet-market-table-dialog.js: keep only engine_type dataset; remove family/category references.
js = DIALOG.read_text()

# Remove obsolete data attributes if previous patches added them.
js = re.sub(r'\n\s*data-aircraft-family="\$\{escapeHtml\(row\.aircraft_family \|\| ""\)\}"', '', js)
js = re.sub(r'\n\s*data-aircraft-category="\$\{escapeHtml\(row\.aircraft_category \|\| ""\)\}"', '', js)

# Remove obsolete detail rows.
js = re.sub(r'\n\s*\$\{detailRow\("Family",\s*model\.aircraft_family\)\}', '', js)
js = re.sub(r'\n\s*\$\{detailRow\("Category",\s*model\.aircraft_category\)\}', '', js)

# Ensure an engine row is visible in aircraft details if the dialog has technical rows.
if 'detailRow("Engine", model.engine_type)' not in js and 'detailRow("Role", model.operation_role)' in js:
    js = js.replace(
        '${detailRow("Role", model.operation_role)}',
        '${detailRow("Role", model.operation_role)}\n            ${detailRow("Engine", model.engine_type)}',
        1,
    )

# Ensure table rows carry data-aircraft-engine.
if 'data-aircraft-engine=' not in js:
    pattern = '            <tr>\n'
    replacement = (
        '            <tr\n'
        '              data-aircraft-icao="${escapeHtml(row.icao_type_code || row.model_code || "")}"\n'
        '              data-aircraft-engine="${escapeHtml(row.engine_type || "")}"\n'
        '              data-aircraft-price="${escapeHtml(row.new_purchase_price ?? row.base_purchase_price ?? "")}"\n'
        '              data-aircraft-pax="${escapeHtml(row.passenger_capacity_standard ?? row.passenger_capacity_max ?? "")}"\n'
        '              data-aircraft-search="${escapeHtml([row.manufacturer, row.model_name, row.model_code, row.icao_type_code, row.iata_type_code, row.engine_type].filter(Boolean).join(" "))}"\n'
        '            >\n'
    )
    if pattern not in js:
        raise SystemExit('Could not safely find aircraft market <tr> insertion point')
    js = js.replace(pattern, replacement, 1)
else:
    # Keep search index aligned with remaining fields only.
    js = re.sub(
        r'\[row\.manufacturer, row\.model_name, row\.model_code, row\.icao_type_code, row\.iata_type_code, row\.aircraft_family, row\.engine_type, row\.aircraft_category\]',
        '[row.manufacturer, row.model_name, row.model_code, row.icao_type_code, row.iata_type_code, row.engine_type]',
        js,
    )
    js = re.sub(
        r'\[row\.manufacturer, row\.model_name, row\.model_code, row\.icao_type_code, row\.iata_type_code, row\.aircraft_family, row\.engine_type\]',
        '[row.manufacturer, row.model_name, row.model_code, row.icao_type_code, row.iata_type_code, row.engine_type]',
        js,
    )

DIALOG.write_text(js)

# 3) aircraft-market-filters.js: rewrite as engine_type-only live filter.
FILTERS.write_text(r'''(() => {
  "use strict";

  const BUY_DIALOG_SELECTOR = "#buyAircraftDialog";
  const FILTER_ID = "aircraftMarketFilters";

  const ENGINE_GROUPS = {
    JET: ["TURBOFAN", "TURBOJET", "JET"],
    TURBOFAN: ["TURBOFAN"],
    TURBOJET: ["TURBOJET"],
    TURBOPROP: ["TURBOPROP"],
    PISTON: ["PISTON"],
    TURBOSHAFT: ["TURBOSHAFT", "HELICOPTER"],
    SUPERSONIC: ["SUPERSONIC"]
  };

  let scheduled = false;

  document.addEventListener("DOMContentLoaded", () => {
    installObserver();
    installDelegatedFilterEvents();
    scheduleRefresh();
  });

  function installObserver() {
    const observer = new MutationObserver(() => scheduleRefresh());
    observer.observe(document.body, { childList: true, subtree: true });
  }

  function installDelegatedFilterEvents() {
    document.addEventListener("input", event => {
      if (event.target?.closest?.(`#${FILTER_ID}`)) {
        scheduleRefresh();
      }
    });

    document.addEventListener("change", event => {
      if (event.target?.closest?.(`#${FILTER_ID}`)) {
        scheduleRefresh();
      }
    });
  }

  function scheduleRefresh() {
    if (scheduled) {
      return;
    }

    scheduled = true;

    window.requestAnimationFrame(() => {
      scheduled = false;

      try {
        ensureFiltersOnBuyDialog();
        applyAircraftMarketFilters();
      } catch (error) {
        console.error("Aircraft market filters failed", error);
      }
    });
  }

  function ensureFiltersOnBuyDialog() {
    const dialog = findVisibleBuyDialog();
    const container = findMarketContainer(dialog);

    if (!dialog || !container) {
      return;
    }

    let filters = dialog.querySelector(`#${FILTER_ID}`);

    if (filters) {
      return;
    }

    filters = document.createElement("section");
    filters.id = FILTER_ID;
    filters.className = "aircraft-market-filters";
    filters.innerHTML = `
      <div class="aircraft-market-filter-grid">
        <label>
          <span>ICAO</span>
          <input type="search" id="aircraftFilterIcao" autocomplete="off" placeholder="A320, B738, MD82">
        </label>

        <label>
          <span>Search</span>
          <input type="search" id="aircraftFilterText" autocomplete="off" placeholder="Boeing, Airbus, Douglas...">
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
            <option value="JET">Jet</option>
            <option value="TURBOFAN">Turbofan</option>
            <option value="TURBOJET">Turbojet</option>
            <option value="TURBOPROP">Turboprop</option>
            <option value="PISTON">Piston</option>
            <option value="TURBOSHAFT">Turboshaft / helicopter</option>
            <option value="SUPERSONIC">Supersonic</option>
          </select>
        </label>

        <button type="button" id="aircraftFilterClear" class="secondary">Clear</button>
      </div>
    `;

    container.parentNode.insertBefore(filters, container);

    filters.querySelector("#aircraftFilterClear")?.addEventListener("click", () => {
      filters.querySelectorAll("input").forEach(input => { input.value = ""; });
      filters.querySelectorAll("select").forEach(select => { select.value = ""; });
      scheduleRefresh();
    });
  }

  function applyAircraftMarketFilters() {
    const dialog = findVisibleBuyDialog();
    const filters = dialog?.querySelector(`#${FILTER_ID}`);
    const container = findMarketContainer(dialog);

    if (!filters || !container) {
      return;
    }

    const criteria = readCriteria(filters);
    const rows = findAircraftRows(container);

    for (const row of rows) {
      setRowVisible(row, matchesCriteria(extractAircraftRowData(row), criteria));
    }
  }

  function readCriteria(filters) {
    return {
      icao: valueOf(filters, "#aircraftFilterIcao").toUpperCase(),
      text: valueOf(filters, "#aircraftFilterText").toLowerCase(),
      maxPrice: numberOrNull(valueOf(filters, "#aircraftFilterMaxPrice")),
      minPax: numberOrNull(valueOf(filters, "#aircraftFilterMinPax")),
      maxPax: numberOrNull(valueOf(filters, "#aircraftFilterMaxPax")),
      engine: normalizeCode(valueOf(filters, "#aircraftFilterEngine"))
    };
  }

  function valueOf(root, selector) {
    return String(root.querySelector(selector)?.value || "").trim();
  }

  function numberOrNull(value) {
    if (value === "") {
      return null;
    }

    const number = Number(value);
    return Number.isFinite(number) ? number : null;
  }

  function findVisibleBuyDialog() {
    const dialog = document.querySelector(BUY_DIALOG_SELECTOR);

    if (!dialog || !isVisibleEnough(dialog)) {
      return null;
    }

    return dialog;
  }

  function findMarketContainer(dialog) {
    if (!dialog) {
      return null;
    }

    return dialog.querySelector("#aircraftMarketTableBody")
      || dialog.querySelector("#aircraftCatalogList")
      || null;
  }

  function findAircraftRows(container) {
    if (!container) {
      return [];
    }

    if (container.tagName?.toUpperCase() === "TBODY") {
      return Array.from(container.children)
        .filter(row => row.tagName?.toUpperCase() === "TR" && row.querySelector("td"));
    }

    return Array.from(container.querySelectorAll("tbody tr, tr"))
      .filter(row => row.querySelector("td"));
  }

  function extractAircraftRowData(row) {
    const text = normalize(row.dataset.aircraftSearch || row.textContent);
    const upper = text.toUpperCase();

    return {
      text,
      upper,
      icao: normalizeCode(row.dataset.aircraftIcao || extractIcao(row, upper)),
      price: numberOrNull(row.dataset.aircraftPrice || "") ?? extractPrice(upper),
      pax: numberOrNull(row.dataset.aircraftPax || "") ?? extractPassengerCapacity(upper),
      engine: normalizeCode(row.dataset.aircraftEngine || "")
    };
  }

  function matchesCriteria(data, criteria) {
    if (criteria.icao && !data.icao.includes(criteria.icao) && !data.upper.includes(criteria.icao)) {
      return false;
    }

    if (criteria.text && !data.text.toLowerCase().includes(criteria.text)) {
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

    if (criteria.engine && !engineMatches(data.engine, criteria.engine)) {
      return false;
    }

    return true;
  }

  function engineMatches(actualEngine, selectedEngine) {
    const normalizedActual = normalizeCode(actualEngine);
    const normalizedSelected = normalizeCode(selectedEngine);

    if (!normalizedSelected) {
      return true;
    }

    const allowedValues = ENGINE_GROUPS[normalizedSelected] || [normalizedSelected];
    return allowedValues.includes(normalizedActual);
  }

  function setRowVisible(row, visible) {
    row.hidden = !visible;
    row.classList.toggle("aircraft-market-filter-hidden", !visible);
  }

  function extractIcao(row, upperText) {
    const firstCell = normalize(row.querySelector("td")?.textContent || "").toUpperCase();

    if (/^[A-Z0-9]{3,5}$/.test(firstCell)) {
      return firstCell;
    }

    const match = upperText.match(/\b[A-Z][A-Z0-9]{2,4}\b/);
    return match ? match[0] : "";
  }

  function extractPrice(upperText) {
    const moneyMatches = Array.from(upperText.matchAll(/(?:EUR|€)?\s*([0-9][0-9., ]{2,})(?:\s*(?:EUR|€))?/g));

    if (!moneyMatches.length) {
      return null;
    }

    const numbers = moneyMatches
      .map(match => parseFlexibleNumber(match[1]))
      .filter(number => Number.isFinite(number) && number > 0);

    return numbers.length ? Math.max(...numbers) : null;
  }

  function extractPassengerCapacity(upperText) {
    const patterns = [
      /(?:PAX|PASSENGERS?|CAPACITY)\D{0,12}([0-9]{1,4})/,
      /([0-9]{1,4})\s*(?:PAX|PASSENGERS?)/
    ];

    for (const pattern of patterns) {
      const match = upperText.match(pattern);

      if (match) {
        const value = Number(match[1]);

        if (Number.isFinite(value)) {
          return value;
        }
      }
    }

    return null;
  }

  function parseFlexibleNumber(raw) {
    let value = String(raw || "").replace(/\s/g, "");

    if (value.includes(",") && value.includes(".")) {
      value = value.replace(/,/g, "");
    } else if (value.includes(",") && !value.includes(".")) {
      value = value.replace(",", ".");
    }

    value = value.replace(/[^0-9.]/g, "");
    return Number(value);
  }

  function normalizeCode(value) {
    return String(value || "").trim().replace(/[\s-]+/g, "_").toUpperCase();
  }

  function normalize(value) {
    return String(value || "").replace(/\s+/g, " ").trim();
  }

  function isVisibleEnough(element) {
    if (!element?.isConnected) {
      return false;
    }

    const style = window.getComputedStyle(element);
    return style.display !== "none" && style.visibility !== "hidden";
  }
})();
''')

DOC.parent.mkdir(parents=True, exist_ok=True)
DOC.write_text('''# Aircraft market engine type only

This patch aligns the Buy new aircraft filters with the database cleanup.

## Database

Migration `120_remove_aircraft_family_category_and_fix_engine_filter.sql`:

- sets Concorde rows to `engine_type = SUPERSONIC`;
- removes `aircraft_family` from `aircraft_models` if present;
- removes `aircraft_category` from `aircraft_models` if present.

## Frontend/API

- `catalog.php` no longer selects removed columns.
- The market row dataset uses `engine_type` as the only engine filter source.
- The Family filter is removed.
- The Engine filter contains Jet, Turbofan, Turbojet, Turboprop, Piston, Turboshaft/helicopter, and Supersonic.
- `Engine: Jet` matches `TURBOFAN`, `TURBOJET`, and legacy `JET` values.
- `Engine: Supersonic` matches `SUPERSONIC`.
''')

print('Patched aircraft market to use engine_type only and removed family/category UI dependencies.')
