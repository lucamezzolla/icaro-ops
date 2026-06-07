(() => {
  const MARKET_CONTAINER_SELECTORS = [
    "#aircraftMarketTableBody",
    "#aircraftCatalogList"
  ];

  const FILTER_ID = "aircraftMarketFilters";

  document.addEventListener("DOMContentLoaded", () => {
    installObserver();
    window.setInterval(ensureFiltersOnVisibleMarket, 500);
  });

  function installObserver() {
    const observer = new MutationObserver(() => {
      ensureFiltersOnVisibleMarket();
      applyAircraftMarketFilters();
    });

    observer.observe(document.body, {
      childList: true,
      subtree: true
    });
  }

  function ensureFiltersOnVisibleMarket() {
    const container = findMarketContainer();

    if (!container) {
      return;
    }

    if (document.querySelector(`#${FILTER_ID}`)) {
      return;
    }

    const filters = document.createElement("section");
    filters.id = FILTER_ID;
    filters.className = "aircraft-market-filters";
    filters.innerHTML = `
      <div class="aircraft-market-filter-grid">
        <label>
          <span>ICAO</span>
          <input type="search" id="aircraftFilterIcao" autocomplete="off">
        </label>

        <label>
          <span>Search</span>
          <input type="search" id="aircraftFilterText" autocomplete="off">
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
            <option value=""></option>
            <option value="FIXED_WING">Fixed wing</option>
            <option value="HELICOPTER">Helicopter</option>
          </select>
        </label>

        <label>
          <span>Engine</span>
          <select id="aircraftFilterEngine">
            <option value=""></option>
            <option value="PISTON">Piston</option>
            <option value="TURBOPROP">Turboprop</option>
            <option value="JET">Jet</option>
            <option value="TURBOSHAFT">Turboshaft</option>
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

    filters.querySelector("#aircraftFilterClear").addEventListener("click", () => {
      filters.querySelectorAll("input").forEach(input => input.value = "");
      filters.querySelectorAll("select").forEach(select => select.value = "");
      applyAircraftMarketFilters();
    });

    applyAircraftMarketFilters();
  }

  function findMarketContainer() {
    for (const selector of MARKET_CONTAINER_SELECTORS) {
      const container = document.querySelector(selector);

      if (container && isVisibleEnough(container)) {
        return container;
      }
    }

    return null;
  }

  function applyAircraftMarketFilters() {
    const filters = document.querySelector(`#${FILTER_ID}`);
    const container = findMarketContainer();

    if (!filters || !container) {
      return;
    }

    const criteria = readCriteria(filters);
    const hasFilters = Object.values(criteria).some(value => value !== "" && value !== null);

    const rows = findAircraftRows(container);

    for (const row of rows) {
      if (!hasFilters) {
        row.hidden = true;
        row.classList.add("aircraft-market-filter-hidden");
        continue;
      }

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
      family: valueOf(filters, "#aircraftFilterFamily").toUpperCase(),
      engine: valueOf(filters, "#aircraftFilterEngine").toUpperCase()
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
    const tableRows = Array.from(container.querySelectorAll("tbody tr, table tr"))
      .filter(row => row.querySelector("td"));

    if (tableRows.length) {
      return tableRows;
    }

    const cards = Array.from(container.querySelectorAll(".aircraft-card, .catalog-card, .market-card, article, li"))
      .filter(card => card.textContent && (
        card.querySelector("[data-aircraft-buy], [data-buy-model], button") ||
        /icao|price|pax|passenger|engine|family/i.test(card.textContent)
      ));

    if (cards.length) {
      return cards;
    }

    return Array.from(container.children).filter(child => child.textContent?.trim());
  }

  function extractAircraftRowData(row) {
    const text = normalize(row.textContent);
    const upper = text.toUpperCase();

    return {
      text,
      upper,
      icao: extractIcao(row, upper),
      price: extractPrice(upper),
      pax: extractPassengerCapacity(upper),
      family: extractOneOf(upper, ["FIXED_WING", "FIXED WING", "HELICOPTER"]),
      engine: extractOneOf(upper, ["PISTON", "TURBOPROP", "JET", "TURBOSHAFT"])
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

    if (criteria.family) {
      const normalizedFamily = data.family.replace(" ", "_");

      if (normalizedFamily !== criteria.family && !data.upper.includes(criteria.family)) {
        return false;
      }
    }

    if (criteria.engine && data.engine !== criteria.engine && !data.upper.includes(criteria.engine)) {
      return false;
    }

    return true;
  }

  function extractIcao(row, upperText) {
    const explicit = row.querySelector("[data-icao], [data-icao-type-code]");

    if (explicit) {
      return String(explicit.dataset.icao || explicit.dataset.icaoTypeCode || "").toUpperCase();
    }

    const cells = Array.from(row.querySelectorAll("td, span, strong, small"))
      .map(cell => normalize(cell.textContent).toUpperCase())
      .filter(Boolean);

    for (const value of cells) {
      if (/^[A-Z0-9]{3,5}$/.test(value)) {
        return value;
      }
    }

    const match = upperText.match(/\b[A-Z][A-Z0-9]{2,4}\b/);

    return match ? match[0] : "";
  }

  function extractPrice(upperText) {
    const moneyMatches = Array.from(upperText.matchAll(/(?:EUR|\€)?\s*([0-9][0-9., ]{2,})(?:\s*(?:EUR|\€))?/g));

    if (!moneyMatches.length) {
      return null;
    }

    const numbers = moneyMatches
      .map(match => parseFlexibleNumber(match[1]))
      .filter(number => Number.isFinite(number) && number > 0);

    if (!numbers.length) {
      return null;
    }

    return Math.max(...numbers);
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

  function extractOneOf(upperText, values) {
    return values.find(value => upperText.includes(value)) || "";
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

  function normalize(value) {
    return String(value || "").replace(/\s+/g, " ").trim();
  }

  function isVisibleEnough(element) {
    if (!element.isConnected) {
      return false;
    }

    const style = window.getComputedStyle(element);

    return style.display !== "none" && style.visibility !== "hidden";
  }
})();
