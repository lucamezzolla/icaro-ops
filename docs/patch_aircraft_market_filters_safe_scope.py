#!/usr/bin/env python3
from pathlib import Path

ROOT = Path.cwd()
FILTERS = ROOT / 'src/js/aircraft-market-filters.js'
DOC = ROOT / 'docs/AIRCRAFT_MARKET_FILTERS_SAFE_SCOPE.md'

if not FILTERS.exists():
    raise SystemExit(f'Missing file: {FILTERS}')

FILTERS.write_text(r'''(() => {
  "use strict";

  const BUY_DIALOG_SELECTOR = "#buyAircraftDialog";
  const FILTER_ID = "aircraftMarketFilters";

  const ENGINE_GROUPS = {
    JET: ["TURBOFAN", "TURBOJET", "JET"],
    TURBOPROP: ["TURBOPROP"],
    PISTON: ["PISTON"],
    HELICOPTER: ["TURBOSHAFT", "HELICOPTER"],
    ELECTRIC: ["ELECTRIC", "HYBRID_ELECTRIC"]
  };

  let scheduled = false;

  document.addEventListener("DOMContentLoaded", () => {
    installObserver();
    scheduleRefresh();
  });

  function installObserver() {
    const observer = new MutationObserver(() => scheduleRefresh());
    observer.observe(document.body, { childList: true, subtree: true });
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
        refreshFamilyOptions();
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

    if (!filters) {
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
            <span>Family</span>
            <select id="aircraftFilterFamily">
              <option value="">All families</option>
            </select>
          </label>

          <label>
            <span>Engine</span>
            <select id="aircraftFilterEngine">
              <option value="">All engines</option>
              <option value="JET">Jet</option>
              <option value="TURBOPROP">Turboprop</option>
              <option value="PISTON">Piston</option>
              <option value="HELICOPTER">Helicopter</option>
              <option value="ELECTRIC">Electric</option>
            </select>
          </label>

          <button type="button" id="aircraftFilterClear" class="secondary">Clear</button>
        </div>
      `;

      container.parentNode.insertBefore(filters, container);

      filters.querySelectorAll("input, select").forEach(input => {
        input.addEventListener("input", applyAircraftMarketFilters);
        input.addEventListener("change", applyAircraftMarketFilters);
      });

      filters.querySelector("#aircraftFilterClear")?.addEventListener("click", () => {
        filters.querySelectorAll("input").forEach(input => { input.value = ""; });
        filters.querySelectorAll("select").forEach(select => { select.value = ""; });
        refreshFamilyOptions();
        applyAircraftMarketFilters();
      });
    }
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

  function refreshFamilyOptions() {
    const dialog = findVisibleBuyDialog();
    const filters = dialog?.querySelector(`#${FILTER_ID}`);
    const familySelect = filters?.querySelector("#aircraftFilterFamily");
    const container = findMarketContainer(dialog);

    if (!familySelect || !container) {
      return;
    }

    const currentValue = familySelect.value;
    const families = Array.from(new Set(findAircraftRows(container)
      .map(row => normalizeCode(row.dataset.aircraftFamily || ""))
      .filter(Boolean)))
      .sort((a, b) => familyLabel(a).localeCompare(familyLabel(b)));

    familySelect.innerHTML = '<option value="">All families</option>' + families
      .map(family => `<option value="${escapeHtml(family)}">${escapeHtml(familyLabel(family))}</option>`)
      .join("");

    if (families.includes(currentValue)) {
      familySelect.value = currentValue;
    }
  }

  function applyAircraftMarketFilters() {
    const dialog = findVisibleBuyDialog();
    const filters = dialog?.querySelector(`#${FILTER_ID}`);
    const container = findMarketContainer(dialog);

    if (!filters || !container) {
      return;
    }

    const criteria = readCriteria(filters);
    const hasFilters = Object.values(criteria).some(value => value !== "" && value !== null);
    const rows = findAircraftRows(container);

    for (const row of rows) {
      if (!hasFilters) {
        setRowVisible(row, false);
        continue;
      }

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
      family: normalizeCode(valueOf(filters, "#aircraftFilterFamily")),
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

  function findAircraftRows(container) {
    if (!container) {
      return [];
    }

    const tagName = container.tagName.toUpperCase();

    if (tagName === "TBODY") {
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
      family: normalizeCode(row.dataset.aircraftFamily || ""),
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

    if (criteria.family && data.family !== criteria.family) {
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

    const group = ENGINE_GROUPS[normalizedSelected] || [normalizedSelected];
    return group.includes(normalizedActual);
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

  function familyLabel(value) {
    const normalized = normalizeCode(value);

    if (!normalized) {
      return "Unknown";
    }

    const label = normalized
      .replace(/_FAMILY$/, "")
      .replace(/_/g, " ")
      .toLowerCase()
      .replace(/\b\w/g, letter => letter.toUpperCase());

    return normalized.endsWith("_FAMILY") ? `${label} family` : label;
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

  function escapeHtml(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }
})();
''')

DOC.parent.mkdir(parents=True, exist_ok=True)
DOC.write_text('''# Aircraft market filters safe scope

This patch makes the Buy new aircraft filters safe for the Fleet page.

## Why

The previous filter script could run against the page too broadly and could fail or interfere with Fleet initialization.

## Changes

- The filter logic now runs only inside `#buyAircraftDialog`.
- It no longer scans every table on the Fleet page.
- It handles `#aircraftMarketTableBody` correctly when the container itself is a `<tbody>`.
- Errors are caught and logged instead of blocking the Fleet page.
- The market still starts empty until at least one filter is selected.
- `Engine: Jet` still includes `TURBOFAN` and `TURBOJET`.
''')

print('Patched src/js/aircraft-market-filters.js with safe dialog-scoped filters.')
