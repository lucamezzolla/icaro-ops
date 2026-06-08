#!/usr/bin/env python3
from pathlib import Path

PROJECT = Path.cwd()
FLEET_JS = PROJECT / "src/js/fleet.js"
FLEET_CSS = PROJECT / "src/css/fleet.css"

def read(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path}")
    return path.read_text(encoding="utf-8")

def write(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")

def find_function_span(content: str, function_name: str):
    markers = [
        f"async function {function_name}(",
        f"function {function_name}(",
    ]

    start = -1
    for marker in markers:
        start = content.find(marker)
        if start >= 0:
            break

    if start < 0:
        return None

    brace = content.find("{", start)
    if brace < 0:
        return None

    depth = 0
    i = brace
    in_string = None
    escape = False
    in_line_comment = False
    in_block_comment = False
    template_depth = 0

    while i < len(content):
        ch = content[i]
        nxt = content[i + 1] if i + 1 < len(content) else ""

        if in_line_comment:
            if ch == "\n":
                in_line_comment = False
            i += 1
            continue

        if in_block_comment:
            if ch == "*" and nxt == "/":
                in_block_comment = False
                i += 2
                continue
            i += 1
            continue

        if in_string:
            if escape:
                escape = False
                i += 1
                continue

            if ch == "\\":
                escape = True
                i += 1
                continue

            if in_string == "`":
                if ch == "$" and nxt == "{":
                    template_depth += 1
                    i += 2
                    continue
                if ch == "}" and template_depth > 0:
                    template_depth -= 1
                    i += 1
                    continue
                if ch == "`" and template_depth == 0:
                    in_string = None
                    i += 1
                    continue
            elif ch == in_string:
                in_string = None
                i += 1
                continue

            i += 1
            continue

        if ch == "/" and nxt == "/":
            in_line_comment = True
            i += 2
            continue

        if ch == "/" and nxt == "*":
            in_block_comment = True
            i += 2
            continue

        if ch in ("'", '"', "`"):
            in_string = ch
            i += 1
            continue

        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return start, i + 1

        i += 1

    return None

def replace_function(content: str, function_name: str, replacement: str) -> str:
    span = find_function_span(content, function_name)
    if not span:
        raise RuntimeError(f"Function not found or not parseable: {function_name}")

    start, end = span
    return content[:start] + replacement.rstrip() + content[end:]

def insert_helpers(content: str, helpers: str) -> str:
    if "function renderAircraftMarketFilters(" in content:
        return content

    markers = [
        "\nasync function openCatalogModelDetail(",
        "\nfunction openCatalogModelDetail(",
        "\nasync function buyAircraft(",
        "\nfunction buyAircraft(",
        "\nfunction closeDialogIfOpen(",
        "\nasync function getJson(",
        "\nfunction showFleetError(",
    ]

    for marker in markers:
        if marker in content:
            return content.replace(marker, "\n" + helpers.rstrip() + "\n" + marker, 1)

    return content.rstrip() + "\n\n" + helpers.rstrip() + "\n"

def patch_js() -> None:
    js = read(FLEET_JS)

    if "let catalogFilterState" not in js:
        if "let catalogAircraft = [];" not in js:
            raise RuntimeError("Unable to find catalogAircraft state declaration.")
        js = js.replace(
            "let catalogAircraft = [];",
            'let catalogAircraft = [];\nlet catalogFilterState = {\n  search: "",\n  manufacturer: "",\n  engineType: "",\n  maxPrice: ""\n};',
            1
        )

    render_catalog = '''function renderCatalog(rows, pilotCoverage = {}) {
  const list = document.querySelector("#aircraftCatalogList");
  const activeRows = rows.filter(isCatalogAircraftActive);
  const filteredRows = filteredCatalogRows(activeRows);

  if (!activeRows.length) {
    list.innerHTML = `<p class="muted">No aircraft available for your current level.</p>`;
    return;
  }

  list.innerHTML = `
    ${renderAircraftMarketFilters(activeRows, filteredRows.length)}
    ${
      filteredRows.length
        ? renderAircraftMarketTable(filteredRows)
        : `<p class="muted">No aircraft match the current filters.</p>`
    }
  `;

  wireAircraftMarketFilters(list);

  list.querySelectorAll("[data-buy-model]").forEach(button => {
    button.addEventListener("click", () => buyAircraft(Number(button.dataset.buyModel)));
  });

  list.querySelectorAll("[data-model-detail]").forEach(button => {
    button.addEventListener("click", () => openCatalogModelDetail(Number(button.dataset.modelDetail)));
  });
}'''

    js = replace_function(js, "renderCatalog", render_catalog)

    helpers = '''function isCatalogAircraftActive(a) {
  const value = a.is_active;

  if (value === undefined || value === null || value === "") {
    return true;
  }

  return Number(value) === 1 || value === true || String(value).toLowerCase() === "true";
}

function renderAircraftMarketFilters(rows, visibleCount) {
  const manufacturers = uniqueSorted(rows.map(a => a.manufacturer).filter(Boolean));
  const engineTypes = uniqueSorted(rows.map(a => a.engine_type || a.engine || a.engine_family).filter(Boolean));

  return `
    <section class="aircraft-market-filter-panel" aria-label="Aircraft market filters">
      <div class="aircraft-market-filters">
        <label>
          <span>Search</span>
          <input
            type="search"
            id="aircraftMarketSearch"
            placeholder="Model, manufacturer, ICAO..."
            value="${escapeHtml(catalogFilterState.search)}"
          >
        </label>

        <label>
          <span>Manufacturer</span>
          <select id="aircraftMarketManufacturer">
            <option value="">All manufacturers</option>
            ${manufacturers.map(value => `
              <option value="${escapeHtml(value)}" ${catalogFilterState.manufacturer === value ? "selected" : ""}>
                ${escapeHtml(value)}
              </option>
            `).join("")}
          </select>
        </label>

        <label>
          <span>Engine</span>
          <select id="aircraftMarketEngine">
            <option value="">All engines</option>
            ${engineTypes.map(value => `
              <option value="${escapeHtml(value)}" ${catalogFilterState.engineType === value ? "selected" : ""}>
                ${escapeHtml(value)}
              </option>
            `).join("")}
          </select>
        </label>

        <label>
          <span>Max price</span>
          <input
            type="number"
            id="aircraftMarketMaxPrice"
            min="0"
            step="1000"
            placeholder="No limit"
            value="${escapeHtml(catalogFilterState.maxPrice)}"
          >
        </label>

        <button type="button" class="secondary" id="aircraftMarketClearFilters">Clear filters</button>
      </div>

      <p class="muted aircraft-market-filter-summary">
        Showing ${visibleCount} of ${rows.length} active aircraft.
      </p>
    </section>
  `;
}

function renderAircraftMarketTable(rows) {
  return `
    <div class="table-wrap catalog-table-wrap">
      <table>
        <thead>
          <tr>
            <th>Aircraft</th>
            <th>ICAO</th>
            <th>Engine</th>
            <th>Capacity</th>
            <th>Range</th>
            <th>Cruise</th>
            <th>Price</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          ${rows.map(a => `
            <tr>
              <td><strong>${escapeHtml(a.manufacturer)} ${escapeHtml(a.model_name)}</strong></td>
              <td>${escapeHtml(a.icao_type_code || "-")}</td>
              <td>${escapeHtml(a.engine_type || a.engine || a.engine_family || "-")}</td>
              <td>${escapeHtml(a.passenger_capacity_standard ?? "-")}</td>
              <td>${escapeHtml(a.range_km ?? "-")} km</td>
              <td>${escapeHtml(a.cruise_speed_kmh ?? "-")} km/h</td>
              <td>${money(a.new_purchase_price || 0)} ${escapeHtml(a.currency_code || "EUR")}</td>
              <td>
                <div class="button-row">
                  <button type="button" data-model-detail="${resolveAircraftModelId(a) || ""}">Details</button>
                  <button type="button" data-buy-model="${a.aircraft_model_id || a.id}" class="secondary">Buy</button>
                </div>
              </td>
            </tr>
          `).join("")}
        </tbody>
      </table>
    </div>
  `;
}

function wireAircraftMarketFilters(root) {
  const search = root.querySelector("#aircraftMarketSearch");
  const manufacturer = root.querySelector("#aircraftMarketManufacturer");
  const engine = root.querySelector("#aircraftMarketEngine");
  const maxPrice = root.querySelector("#aircraftMarketMaxPrice");
  const clear = root.querySelector("#aircraftMarketClearFilters");

  const refresh = () => renderCatalog(catalogAircraft);

  search?.addEventListener("input", () => {
    catalogFilterState.search = search.value;
    refresh();
  });

  manufacturer?.addEventListener("change", () => {
    catalogFilterState.manufacturer = manufacturer.value;
    refresh();
  });

  engine?.addEventListener("change", () => {
    catalogFilterState.engineType = engine.value;
    refresh();
  });

  maxPrice?.addEventListener("input", () => {
    catalogFilterState.maxPrice = maxPrice.value;
    refresh();
  });

  clear?.addEventListener("click", () => {
    catalogFilterState = {
      search: "",
      manufacturer: "",
      engineType: "",
      maxPrice: ""
    };

    refresh();
  });
}

function filteredCatalogRows(rows) {
  const query = catalogFilterState.search.trim().toLowerCase();
  const manufacturer = catalogFilterState.manufacturer;
  const engineType = catalogFilterState.engineType;
  const maxPrice = Number(catalogFilterState.maxPrice);

  return rows.filter(a => {
    if (manufacturer && a.manufacturer !== manufacturer) {
      return false;
    }

    const rowEngine = a.engine_type || a.engine || a.engine_family || "";

    if (engineType && rowEngine !== engineType) {
      return false;
    }

    if (Number.isFinite(maxPrice) && maxPrice > 0 && Number(a.new_purchase_price || 0) > maxPrice) {
      return false;
    }

    if (!query) {
      return true;
    }

    const haystack = [
      a.manufacturer,
      a.model_name,
      a.model_code,
      a.icao_type_code,
      a.engine_type,
      a.engine,
      a.engine_family,
      a.operation_role
    ].join(" ").toLowerCase();

    return haystack.includes(query);
  });
}

function uniqueSorted(values) {
  return [...new Set(values.map(value => String(value || "").trim()).filter(Boolean))]
    .sort((a, b) => a.localeCompare(b, undefined, { sensitivity: "base" }));
}'''

    js = insert_helpers(js, helpers)

    write(FLEET_JS, js)

def patch_css() -> None:
    css = read(FLEET_CSS)

    append = '''

/* Aircraft market filters */
.aircraft-market-filter-panel {
  margin: 0 0 1rem;
  padding: 1rem;
  border: 1px solid rgba(255,255,255,.12);
  border-radius: 16px;
  background: rgba(255,255,255,.04);
}

.aircraft-market-filters {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: .75rem;
  align-items: end;
}

.aircraft-market-filters label {
  display: flex;
  flex-direction: column;
  gap: .25rem;
  font-size: .85rem;
}

.aircraft-market-filters input,
.aircraft-market-filters select {
  width: 100%;
}

.aircraft-market-filter-summary {
  margin: .5rem 0 0;
}
'''

    if "/* Aircraft market filters */" not in css:
        css += append

    write(FLEET_CSS, css)

def main() -> None:
    patch_js()
    patch_css()
    print("Aircraft market filters restored.")

if __name__ == "__main__":
    main()
