#!/usr/bin/env python3
from pathlib import Path

path = Path('src/js/fleet.js')
text = path.read_text(encoding='utf-8')
start = text.find('function renderCatalog(rows, pilotCoverage) {')
if start < 0:
    raise SystemExit('Could not find renderCatalog() in src/js/fleet.js')
end = text.find('\nasync function openCatalogModelDetail', start)
if end < 0:
    raise SystemExit('Could not find openCatalogModelDetail() after renderCatalog()')

replacement = """function renderCatalog(rows, pilotCoverage) {
  const list = document.querySelector(\"#aircraftCatalogList\");
  const allRows = Array.isArray(rows) ? rows : [];

  if (!allRows.length) {
    list.innerHTML = `<p class=\"muted\">No aircraft available.</p>`;
    return;
  }

  list.innerHTML = `
    <section class=\"aircraft-market-filter-panel\" aria-label=\"Aircraft market filters\">
      <div class=\"aircraft-market-filters\">
        <label>
          ICAO
          <input id=\"aircraftMarketFilterIcao\" type=\"text\" placeholder=\"A320, B738, CONC\" autocomplete=\"off\">
        </label>
        <label>
          Search
          <input id=\"aircraftMarketFilterSearch\" type=\"text\" placeholder=\"manufacturer or model\" autocomplete=\"off\">
        </label>
        <label>
          Max price
          <input id=\"aircraftMarketFilterMaxPrice\" type=\"number\" min=\"0\" step=\"100000\" placeholder=\"Any\">
        </label>
        <label>
          Min pax
          <input id=\"aircraftMarketFilterMinPax\" type=\"number\" min=\"0\" step=\"1\" placeholder=\"Any\">
        </label>
        <label>
          Max pax
          <input id=\"aircraftMarketFilterMaxPax\" type=\"number\" min=\"0\" step=\"1\" placeholder=\"Any\">
        </label>
        <label>
          Engine
          <select id=\"aircraftMarketFilterEngine\">
            <option value=\"\">All engines</option>
            <option value=\"TURBOFAN\">Turbofan / jet</option>
            <option value=\"TURBOPROP\">Turboprop</option>
            <option value=\"PISTON\">Piston</option>
            <option value=\"TURBOSHAFT\">Turboshaft / helicopter</option>
            <option value=\"SUPERSONIC\">Supersonic</option>
          </select>
        </label>
        <button id=\"aircraftMarketFilterClear\" type=\"button\" class=\"secondary\">Clear</button>
      </div>
      <p id=\"aircraftMarketFilterSummary\" class=\"muted aircraft-market-filter-summary\"></p>
    </section>

    <div class=\"table-wrap catalog-table-wrap\">
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
        <tbody id=\"aircraftCatalogRows\"></tbody>
      </table>
    </div>
  `;

  const tbody = list.querySelector(\"#aircraftCatalogRows\");
  const summary = list.querySelector(\"#aircraftMarketFilterSummary\");
  const filterIcao = list.querySelector(\"#aircraftMarketFilterIcao\");
  const filterSearch = list.querySelector(\"#aircraftMarketFilterSearch\");
  const filterMaxPrice = list.querySelector(\"#aircraftMarketFilterMaxPrice\");
  const filterMinPax = list.querySelector(\"#aircraftMarketFilterMinPax\");
  const filterMaxPax = list.querySelector(\"#aircraftMarketFilterMaxPax\");
  const filterEngine = list.querySelector(\"#aircraftMarketFilterEngine\");
  const clearButton = list.querySelector(\"#aircraftMarketFilterClear\");

  const normalize = value => String(value ?? \"\").trim().toUpperCase();
  const numberOrNull = value => {
    if (value === null || value === undefined || value === \"\") {
      return null;
    }

    const number = Number(value);
    return Number.isFinite(number) ? number : null;
  };

  const rowEngine = row => normalize(row.engine_type || row.engineType);
  const rowIcao = row => normalize(row.icao_type_code || row.model_code || row.iata_type_code);
  const rowPax = row => numberOrNull(row.passenger_capacity_standard ?? row.passenger_capacity_max);
  const rowPrice = row => numberOrNull(row.new_purchase_price ?? row.base_purchase_price ?? aircraftPurchasePriceValue(row));
  const rowText = row => normalize([
    row.manufacturer,
    row.model_name,
    row.model_code,
    row.icao_type_code,
    row.iata_type_code,
    row.operation_role,
    row.engine_type
  ].filter(Boolean).join(\" \"));

  const matchesFilters = row => {
    const icao = normalize(filterIcao.value);
    const search = normalize(filterSearch.value);
    const engine = normalize(filterEngine.value);
    const maxPrice = numberOrNull(filterMaxPrice.value);
    const minPax = numberOrNull(filterMinPax.value);
    const maxPax = numberOrNull(filterMaxPax.value);
    const price = rowPrice(row);
    const pax = rowPax(row);

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

  const bindCatalogButtons = () => {
    tbody.querySelectorAll(\"[data-buy-model]\").forEach(button => {
      button.addEventListener(\"click\", () => buyAircraft(Number(button.dataset.buyModel)));
    });

    tbody.querySelectorAll(\"[data-model-detail]\").forEach(button => {
      button.addEventListener(\"click\", () => openCatalogModelDetail(Number(button.dataset.modelDetail)));
    });
  };

  const renderRows = () => {
    const visibleRows = allRows.filter(matchesFilters);
    summary.textContent = `${visibleRows.length} of ${allRows.length} aircraft shown`;

    if (!visibleRows.length) {
      tbody.innerHTML = `<tr><td colspan=\"8\">No aircraft match the selected filters.</td></tr>`;
      return;
    }

    tbody.innerHTML = visibleRows.map(a => {
      const modelId = resolveAircraftModelId(a) || \"\";
      const engine = rowEngine(a) || \"-\";

      return `
        <tr data-engine-type=\"${escapeHtml(engine)}\" data-aircraft-engine=\"${escapeHtml(engine)}\">
          <td><strong>${escapeHtml(a.manufacturer)} ${escapeHtml(a.model_name)}</strong></td>
          <td>${escapeHtml(a.icao_type_code || \"-\")}</td>
          <td>${escapeHtml(engine)}</td>
          <td>${escapeHtml(a.passenger_capacity_standard ?? a.passenger_capacity_max ?? \"-\")}</td>
          <td>${escapeHtml(a.range_km ?? \"-\")} km</td>
          <td>${escapeHtml(a.cruise_speed_kmh ?? \"-\")} km/h</td>
          <td>${money(a.new_purchase_price || 0)} ${escapeHtml(a.currency_code || \"EUR\")}</td>
          <td>
            <div class=\"button-row\">
              <button type=\"button\" data-model-detail=\"${escapeHtml(modelId)}\">Details</button>
              <button type=\"button\" data-buy-model=\"${escapeHtml(a.aircraft_model_id || a.id || \"\")}\" class=\"secondary\">Buy</button>
            </div>
          </td>
        </tr>
      `;
    }).join(\"\");

    bindCatalogButtons();
  };

  [filterIcao, filterSearch, filterMaxPrice, filterMinPax, filterMaxPax].forEach(input => {
    input.addEventListener(\"input\", renderRows);
  });

  filterEngine.addEventListener(\"change\", renderRows);

  clearButton.addEventListener(\"click\", () => {
    filterIcao.value = \"\";
    filterSearch.value = \"\";
    filterMaxPrice.value = \"\";
    filterMinPax.value = \"\";
    filterMaxPax.value = \"\";
    filterEngine.value = \"\";
    renderRows();
  });

  renderRows();
}


"""

new_text = text[:start] + replacement + text[end+1:]
path.write_text(new_text, encoding='utf-8')
print('Patched src/js/fleet.js: Buy new aircraft filters are now rendered by the active dialog.')
