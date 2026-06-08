#!/usr/bin/env python3
from pathlib import Path
import re

ROOT = Path.cwd()
CATALOG = ROOT / "api/public/fleet/catalog.php"
DIALOG = ROOT / "src/js/fleet-market-table-dialog.js"
FILTERS = ROOT / "src/js/aircraft-market-filters.js"


def patch_catalog():
    text = CATALOG.read_text()
    original = text

    # Ensure engine_type is returned by the catalog endpoint.
    select_marker = "      operation_role,\n"
    if "engine_type" not in text.split("FROM aircraft_models", 1)[0]:
        if select_marker in text:
            text = text.replace(select_marker, select_marker + "      engine_type,\n", 1)
        else:
            raise SystemExit("Could not find operation_role in catalog SELECT")

    if text != original:
        CATALOG.write_text(text)
        print(f"Patched {CATALOG}")
    else:
        print(f"No catalog change needed: {CATALOG}")


def patch_dialog():
    text = DIALOG.read_text()
    original = text

    # Add engine_type as a row data attribute in the market table rows.
    # This avoids filtering by visible text and makes the filter read the DB field.
    if "data-engine-type" not in text:
        text = text.replace(
            "            <tr>\n",
            "            <tr data-engine-type=\"${escapeHtml(row.engine_type || \"\")}\" data-aircraft-engine=\"${escapeHtml(row.engine_type || \"\")}\">\n",
            1,
        )
    else:
        print("Row data-engine-type already present")

    # If a previous patch used data attributes but not the canonical one, leave it alone.
    if text != original:
        DIALOG.write_text(text)
        print(f"Patched {DIALOG}")
    else:
        print(f"No dialog change needed: {DIALOG}")


def patch_filters():
    new_text = r'''(() => {
  const FILTER_ID = "aircraftMarketFilters";
  const MARKET_DIALOG_SELECTOR = "#buyAircraftDialog";
  const MARKET_BODY_SELECTOR = "#aircraftMarketTableBody";

  const ENGINE_OPTIONS = [
    ["", "All engines"],
    ["TURBOFAN", "Turbofan / jet"],
    ["TURBOPROP", "Turboprop"],
    ["PISTON", "Piston"],
    ["TURBOSHAFT", "Turboshaft / helicopter"],
    ["SUPERSONIC", "Supersonic"]
  ];

  document.addEventListener("DOMContentLoaded", () => {
    installMarketFilterObserver();
    ensureFiltersOnMarketDialog();
  });

  function installMarketFilterObserver() {
    const observer = new MutationObserver(() => {
      ensureFiltersOnMarketDialog();
      applyAircraftMarketFilters();
    });

    observer.observe(document.body, {
      childList: true,
      subtree: true
    });
  }

  function ensureFiltersOnMarketDialog() {
    const context = findMarketContext();

    if (!context) {
      return;
    }

    const { dialog, container } = context;

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
          <input type="search" id="aircraftFilterIcao" autocomplete="off" placeholder="A320, B738...">
        </label>

        <label>
          <span>Search</span>
          <input type="search" id="aircraftFilterText" autocomplete="off" placeholder="Boeing, Airbus...">
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
            ${ENGINE_OPTIONS.map(([value, label]) => `<option value="${value}">${label}</option>`).join("")}
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
      filters.querySelectorAll("input").forEach(input => input.value = "");
      filters.querySelectorAll("select").forEach(select => select.value = "");
      applyAircraftMarketFilters();
    });
  }

  function findMarketContext() {
    const dialog = document.querySelector(MARKET_DIALOG_SELECTOR);

    if (!dialog) {
      return null;
    }

    const container = dialog.querySelector(MARKET_BODY_SELECTOR);

    if (!container) {
      return null;
    }

    return { dialog, container };
  }

  function applyAircraftMarketFilters() {
    const context = findMarketContext();

    if (!context) {
      return;
    }

    const { dialog, container } = context;
    const filters = dialog.querySelector(`#${FILTER_ID}`);

    if (!filters) {
      return;
    }

    const criteria = readCriteria(filters);
    const rows = Array.from(container.querySelectorAll("tbody tr, tr")).filter(row => row.querySelector("td"));

    for (const row of rows) {
      const data = extractAircraftRowData(row);
      const visible = matchesCriteria(data, criteria);

      row.hidden = !visible;
      row.classList.toggle("aircraft-market-filter-hidden", !visible);
    }
  }

  function readCriteria(filters) {
    return {
      icao: valueOf(filters, "#aircraftFilterIcao").toUpperCase(),
      text: valueOf(filters, "#aircraftFilterText").toLowerCase(),
      maxPrice: numberOrNull(valueOf(filters, "#aircraftFilterMaxPrice")),
      minPax: numberOrNull(valueOf(filters, "#aircraftFilterMinPax")),
      maxPax: numberOrNull(valueOf(filters, "#aircraftFilterMaxPax")),
      engineType: normalizeEngineType(valueOf(filters, "#aircraftFilterEngine"))
    };
  }

  function extractAircraftRowData(row) {
    const cells = Array.from(row.querySelectorAll("td")).map(cell => normalizeText(cell.textContent));
    const text = normalizeText(row.textContent);
    const upper = text.toUpperCase();

    return {
      text,
      upper,
      icao: normalizeText(cells[0] || "").toUpperCase(),
      price: extractPrice(upper),
      pax: extractPassengerCapacity(cells),
      engineType: normalizeEngineType(row.dataset.engineType || row.dataset.aircraftEngine || "")
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

    if (criteria.engineType && data.engineType !== criteria.engineType) {
      return false;
    }

    return true;
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

  function normalizeText(value) {
    return String(value || "").replace(/\s+/g, " ").trim();
  }

  function normalizeEngineType(value) {
    const normalized = String(value || "").trim().toUpperCase().replace(/[\s-]+/g, "_");

    // Important: there is intentionally no generic JET option here.
    // The filter uses aircraft_models.engine_type exactly.
    const allowed = new Set([
      "TURBOFAN",
      "TURBOPROP",
      "PISTON",
      "TURBOSHAFT",
      "SUPERSONIC",
      "TURBOJET"
    ]);

    return allowed.has(normalized) ? normalized : "";
  }

  function extractPassengerCapacity(cells) {
    if (cells.length >= 3) {
      const pax = parseFlexibleNumber(cells[2]);

      if (Number.isFinite(pax)) {
        return pax;
      }
    }

    return null;
  }

  function extractPrice(upperText) {
    const moneyMatches = Array.from(upperText.matchAll(/(?:EUR|€)?\s*([0-9][0-9., ]{2,})(?:\s*(?:EUR|€))?/g));

    if (!moneyMatches.length) {
      return null;
    }

    const numbers = moneyMatches
      .map(match => parseFlexibleNumber(match[1]))
      .filter(number => Number.isFinite(number) && number > 0);

    return numbers.length ? numbers[numbers.length - 1] : null;
  }

  function parseFlexibleNumber(value) {
    const cleaned = String(value || "").replace(/\s/g, "");

    if (!cleaned) {
      return NaN;
    }

    if (cleaned.includes(",") && cleaned.includes(".")) {
      return Number(cleaned.replace(/,/g, ""));
    }

    if (cleaned.includes(",") && !cleaned.includes(".")) {
      return Number(cleaned.replace(/\./g, "").replace(",", "."));
    }

    return Number(cleaned.replace(/,/g, ""));
  }
})();
'''

    FILTERS.write_text(new_text)
    print(f"Replaced {FILTERS} with exact DB engine-type filter")


def main():
    for path in [CATALOG, DIALOG, FILTERS]:
        if not path.exists():
            raise SystemExit(f"Missing file: {path}")

    patch_catalog()
    patch_dialog()
    patch_filters()
    print("Done. Engine filter now uses aircraft_models.engine_type exact DB values. No generic JET option is rendered.")


if __name__ == "__main__":
    main()
