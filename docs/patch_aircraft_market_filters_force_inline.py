#!/usr/bin/env python3
from pathlib import Path

ROOT = Path.cwd()
CATALOG = ROOT / "api/public/fleet/catalog.php"
DIALOG_JS = ROOT / "src/js/fleet-market-table-dialog.js"
FILTER_JS = ROOT / "src/js/aircraft-market-filters.js"
FLEET_CSS = ROOT / "src/css/fleet.css"


def read(path: Path) -> str:
    if not path.exists():
        raise SystemExit(f"Missing file: {path}")
    return path.read_text(encoding="utf-8")


def write(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def replace_function(source: str, function_name: str, replacement: str) -> str:
    marker = f"function {function_name}("
    start = source.find(marker)
    if start < 0:
        raise SystemExit(f"Could not find function {function_name}() in fleet-market-table-dialog.js")

    brace_start = source.find("{", start)
    if brace_start < 0:
        raise SystemExit(f"Could not find opening brace for {function_name}()")

    depth = 0
    in_string = None
    escape = False
    in_line_comment = False
    in_block_comment = False

    for index in range(brace_start, len(source)):
        char = source[index]
        nxt = source[index + 1] if index + 1 < len(source) else ""

        if in_line_comment:
            if char == "\n":
                in_line_comment = False
            continue

        if in_block_comment:
            if char == "*" and nxt == "/":
                in_block_comment = False
            continue

        if in_string:
            if escape:
                escape = False
                continue
            if char == "\\":
                escape = True
                continue
            if char == in_string:
                in_string = None
            continue

        if char == "/" and nxt == "/":
            in_line_comment = True
            continue
        if char == "/" and nxt == "*":
            in_block_comment = True
            continue
        if char in ('"', "'", "`"):
            in_string = char
            continue
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                end = index + 1
                return source[:start] + replacement.rstrip() + source[end:]

    raise SystemExit(f"Could not find end of function {function_name}()")


def patch_catalog() -> None:
    text = read(CATALOG)
    if "engine_type" not in text:
        needle = "      icao_type_code,\n"
        if needle not in text:
            raise SystemExit("Could not find icao_type_code in catalog.php SELECT")
        text = text.replace(needle, needle + "      engine_type,\n", 1)
    write(CATALOG, text)


def patch_dialog_js() -> None:
    text = read(DIALOG_JS)

    replacement = r'''function renderAircraftTable(container, aircraft) {
    const allAircraft = Array.isArray(aircraft) ? aircraft : [];

    container.innerHTML = `
      <section class="aircraft-market-filter-panel" aria-label="Aircraft market filters">
        <div class="aircraft-market-filters">
          <label>
            ICAO
            <input id="aircraftMarketFilterIcao" type="text" placeholder="A320, B738, CONC" autocomplete="off">
          </label>
          <label>
            Search
            <input id="aircraftMarketFilterSearch" type="text" placeholder="manufacturer or model" autocomplete="off">
          </label>
          <label>
            Max price
            <input id="aircraftMarketFilterMaxPrice" type="number" min="0" step="100000" placeholder="Any">
          </label>
          <label>
            Min pax
            <input id="aircraftMarketFilterMinPax" type="number" min="0" step="1" placeholder="Any">
          </label>
          <label>
            Max pax
            <input id="aircraftMarketFilterMaxPax" type="number" min="0" step="1" placeholder="Any">
          </label>
          <label>
            Engine
            <select id="aircraftMarketFilterEngine">
              <option value="">All engines</option>
              <option value="TURBOFAN">Turbofan / jet</option>
              <option value="TURBOPROP">Turboprop</option>
              <option value="PISTON">Piston</option>
              <option value="TURBOSHAFT">Turboshaft / helicopter</option>
              <option value="SUPERSONIC">Supersonic</option>
            </select>
          </label>
          <button id="aircraftMarketFilterClear" type="button" class="secondary">Clear</button>
        </div>
        <p id="aircraftMarketFilterSummary" class="muted aircraft-market-filter-summary"></p>
      </section>
      <table class="compact-dialog-table aircraft-market-table">
        <thead>
          <tr>
            <th>ICAO</th>
            <th>Aircraft</th>
            <th>Passengers</th>
            <th>Range</th>
            <th>Price</th>
            <th></th>
          </tr>
        </thead>
        <tbody id="aircraftMarketRows"></tbody>
      </table>
    `;

    const filterIcao = container.querySelector("#aircraftMarketFilterIcao");
    const filterSearch = container.querySelector("#aircraftMarketFilterSearch");
    const filterMaxPrice = container.querySelector("#aircraftMarketFilterMaxPrice");
    const filterMinPax = container.querySelector("#aircraftMarketFilterMinPax");
    const filterMaxPax = container.querySelector("#aircraftMarketFilterMaxPax");
    const filterEngine = container.querySelector("#aircraftMarketFilterEngine");
    const clearButton = container.querySelector("#aircraftMarketFilterClear");
    const summary = container.querySelector("#aircraftMarketFilterSummary");
    const tbody = container.querySelector("#aircraftMarketRows");

    const normalized = value => String(value ?? "").trim().toUpperCase();
    const numeric = value => {
      const number = Number(value);
      return Number.isFinite(number) ? number : null;
    };

    const rowEngine = row => normalized(row.engine_type || row.engineType || row.engine || row.data_engine_type);
    const rowIcao = row => normalized(row.icao_type_code || row.icao || row.model_code);
    const rowText = row => normalized([
      row.manufacturer,
      row.model_name,
      row.model_code,
      row.icao_type_code,
      row.iata_type_code,
      row.engine_type
    ].filter(Boolean).join(" "));

    const matchesFilters = row => {
      const icao = normalized(filterIcao.value);
      const search = normalized(filterSearch.value);
      const engine = normalized(filterEngine.value);
      const maxPrice = numeric(filterMaxPrice.value);
      const minPax = numeric(filterMinPax.value);
      const maxPax = numeric(filterMaxPax.value);
      const price = numeric(row.new_purchase_price);
      const pax = numeric(row.passenger_capacity_standard ?? row.passenger_capacity_max);

      if (icao && !rowIcao(row).includes(icao)) {
        return false;
      }

      if (search && !rowText(row).includes(search)) {
        return false;
      }

      if (engine && rowEngine(row) !== engine) {
        return false;
      }

      if (maxPrice !== null && price !== null && price > maxPrice) {
        return false;
      }

      if (minPax !== null && pax !== null && pax < minPax) {
        return false;
      }

      if (maxPax !== null && pax !== null && pax > maxPax) {
        return false;
      }

      return true;
    };

    const bindRowButtons = () => {
      tbody.querySelectorAll("[data-aircraft-detail]").forEach(button => {
        button.addEventListener("click", () => showAircraftDetailFromButton(button));
      });

      tbody.querySelectorAll("[data-aircraft-buy]").forEach(button => {
        button.addEventListener("click", () => buyAircraft(Number(button.dataset.aircraftBuy)));
      });
    };

    const renderRows = () => {
      const visibleAircraft = allAircraft.filter(matchesFilters);

      summary.textContent = `${visibleAircraft.length} of ${allAircraft.length} aircraft shown`;

      if (!visibleAircraft.length) {
        tbody.innerHTML = `<tr><td colspan="6">No aircraft match the selected filters.</td></tr>`;
        return;
      }

      tbody.innerHTML = visibleAircraft.map(row => {
        const modelId = resolveAircraftModelId(row) || "";
        const engine = rowEngine(row);
        const icao = row.icao_type_code || row.model_code || "";

        return `
          <tr data-engine-type="${escapeHtml(engine)}" data-aircraft-engine="${escapeHtml(engine)}">
            <td><strong>${escapeHtml(icao)}</strong></td>
            <td>${escapeHtml(row.manufacturer || "")} ${escapeHtml(row.model_name || "")}</td>
            <td>${escapeHtml(row.passenger_capacity_standard ?? row.passenger_capacity_max ?? "-")}</td>
            <td>${escapeHtml(row.range_km ?? "-")} km</td>
            <td>${money(row.new_purchase_price)} ${escapeHtml(row.currency_code || "")}</td>
            <td>
              <button type="button" data-aircraft-detail="${escapeHtml(modelId)}">Details</button>
              <button type="button" data-aircraft-buy="${escapeHtml(row.aircraft_model_id || row.id || "")}" class="primary">Buy</button>
            </td>
          </tr>
        `;
      }).join("");

      bindRowButtons();
    };

    [filterIcao, filterSearch, filterMaxPrice, filterMinPax, filterMaxPax].forEach(input => {
      input.addEventListener("input", renderRows);
    });
    filterEngine.addEventListener("change", renderRows);

    clearButton.addEventListener("click", () => {
      filterIcao.value = "";
      filterSearch.value = "";
      filterMaxPrice.value = "";
      filterMinPax.value = "";
      filterMaxPax.value = "";
      filterEngine.value = "";
      renderRows();
    });

    renderRows();
  }'''

    text = replace_function(text, "renderAircraftTable", replacement)
    write(DIALOG_JS, text)


def patch_filter_js() -> None:
    if FILTER_JS.exists():
        FILTER_JS.write_text("""(() => {\n  // Aircraft market filters are rendered inline by fleet-market-table-dialog.js.\n  // This file is intentionally passive to avoid duplicate DOM mutations.\n})();\n""", encoding="utf-8")


def patch_css() -> None:
    css = read(FLEET_CSS)
    marker = "/* Aircraft market inline filters */"
    block = r'''
/* Aircraft market inline filters */
.aircraft-market-filter-panel {
  margin-bottom: 1rem;
}

.aircraft-market-filters {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 0.75rem;
  align-items: end;
}

.aircraft-market-filters label {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  font-size: 0.85rem;
}

.aircraft-market-filters input,
.aircraft-market-filters select {
  width: 100%;
}

.aircraft-market-filter-summary {
  margin: 0.5rem 0 0;
}
'''
    if marker not in css:
        css = css.rstrip() + "\n\n" + block.strip() + "\n"
        write(FLEET_CSS, css)


def main() -> None:
    patch_catalog()
    patch_dialog_js()
    patch_filter_js()
    patch_css()
    print("Patched Buy new aircraft filters inline in fleet-market-table-dialog.js.")


if __name__ == "__main__":
    main()
