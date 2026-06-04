const API = {
  currentCompany: companyId => `api/public/company/current.php?companyId=${encodeURIComponent(companyId)}`,
  rivalBases: companyId => `api/public/rivals/bases.php?companyId=${encodeURIComponent(companyId)}`,
  airportSearch: query => `api/public/airports/search.php?q=${encodeURIComponent(query)}`
};

const DEFAULT_WORLD_BOUNDS = L.latLngBounds(
  L.latLng(-58, -170),
  L.latLng(76, 170)
);

let map;
let hqLayer;
let rivalLayer;
let searchLayer;

document.addEventListener("DOMContentLoaded", async () => {
  startUtcClock();
  initMap();
  bindAirportSearch();

  const companyId = resolveCompanyId();

  if (!companyId) {
    setCompanySummaryError("No company found. Create a company first.");
    fitWorldSafely();
    return;
  }

  await loadDashboard(companyId);
});

function initMap() {
  map = L.map("map", {
    worldCopyJump: true,
    minZoom: 2,
    maxZoom: 18,
    zoomControl: true,
    attributionControl: true
  });

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 18,
    noWrap: false,
    updateWhenIdle: true,
    updateWhenZooming: false,
    keepBuffer: 4,
    attribution: "&copy; OpenStreetMap contributors"
  }).addTo(map);

  hqLayer = L.layerGroup().addTo(map);
  rivalLayer = L.layerGroup().addTo(map);
  searchLayer = L.layerGroup().addTo(map);

  fitWorldSafely();

  window.addEventListener("resize", () => {
    map.invalidateSize({ animate: false });
  });

  requestAnimationFrame(() => map.invalidateSize({ animate: false }));
  setTimeout(() => map.invalidateSize({ animate: false }), 150);
  setTimeout(() => map.invalidateSize({ animate: false }), 500);
  setTimeout(() => map.invalidateSize({ animate: false }), 1000);
}

async function loadDashboard(companyId) {
  try {
    const company = await getJson(API.currentCompany(companyId));
    renderCompany(company);
    renderHqMarker(company);
    await renderRivalBases(companyId);

    const airport = company.base_airport;

    if (airport?.latitude && airport?.longitude) {
      map.invalidateSize({ animate: false });
      map.setView([Number(airport.latitude), Number(airport.longitude)], 6);
    } else {
      fitWorldSafely();
    }
  } catch (error) {
    setCompanySummaryError("Unable to load company. Check API, PHP and MySQL configuration.");
    fitWorldSafely();
  }
}

function bindAirportSearch() {
  const form = document.querySelector("#airportSearchForm");
  const input = document.querySelector("#airportSearchInput");
  const results = document.querySelector("#airportSearchResults");

  if (!form || !input || !results) {
    return;
  }

  form.addEventListener("submit", async event => {
    event.preventDefault();

    const query = input.value.trim();

    if (query.length < 2) {
      renderSearchMessage("Type at least 2 characters.");
      return;
    }

    try {
      const rows = await getJson(API.airportSearch(query));
      renderAirportSearchResults(rows);
    } catch {
      renderSearchMessage("Search unavailable. Check API/PHP/MySQL.");
    }
  });

  document.addEventListener("click", event => {
    if (!form.contains(event.target)) {
      results.hidden = true;
    }
  });
}

function renderAirportSearchResults(rows) {
  const results = document.querySelector("#airportSearchResults");
  results.hidden = false;

  if (!rows.length) {
    results.innerHTML = `<div class="search-result"><strong>No airports found</strong><span>Try ICAO, IATA, city or airport name.</span></div>`;
    return;
  }

  results.innerHTML = rows.map((airport, index) => `
    <button type="button" class="search-result" data-index="${index}">
      <strong>${escapeHtml(airport.icao_code)}${airport.iata_code ? " / " + escapeHtml(airport.iata_code) : ""} · ${escapeHtml(airport.airport_name)}</strong>
      <span>${escapeHtml(airport.city || airport.location_name || "Unknown location")} · ${escapeHtml(airport.country_name)} · ${escapeHtml(airport.world_region_name)}</span>
    </button>
  `).join("");

  results.querySelectorAll(".search-result[data-index]").forEach(button => {
    button.addEventListener("click", () => {
      const airport = rows[Number(button.dataset.index)];
      flyToSearchedAirport(airport);
      results.hidden = true;
    });
  });
}

function renderSearchMessage(message) {
  const results = document.querySelector("#airportSearchResults");
  results.hidden = false;
  results.innerHTML = `<div class="search-result"><strong>${escapeHtml(message)}</strong></div>`;
}

function flyToSearchedAirport(airport) {
  if (!airport.latitude || !airport.longitude) {
    renderSearchMessage("Airport found, but coordinates are missing.");
    return;
  }

  searchLayer.clearLayers();

  const latLng = [Number(airport.latitude), Number(airport.longitude)];

  const marker = L.marker(latLng, {
    icon: L.divIcon({
      className: "",
      html: airportIconSvg("search-airport-marker"),
      iconSize: [34, 34],
      iconAnchor: [17, 17],
      popupAnchor: [0, -16]
    })
  });

  marker.bindPopup(`
    <div class="base-popup">
      <h3>${escapeHtml(airport.airport_name)}</h3>
      <p><strong>${escapeHtml(airport.icao_code)}${airport.iata_code ? " / " + escapeHtml(airport.iata_code) : ""}</strong></p>
      <p>${escapeHtml(airport.city || airport.location_name || "")}, ${escapeHtml(airport.country_name)}</p>
      <dl>
        <dt>Type</dt><dd>${escapeHtml(airport.airport_type || "-")}</dd>
        <dt>Service</dt><dd>${escapeHtml(airport.service_category || "-")}</dd>
        <dt>Closed</dt><dd>${airport.is_closed ? "Yes" : "No"}</dd>
      </dl>
    </div>
  `);

  marker.addTo(searchLayer);
  map.setView(latLng, 11);
  marker.openPopup();
}

function fitWorldSafely() {
  if (!map) return;

  map.invalidateSize({ animate: false });
  map.fitBounds(DEFAULT_WORLD_BOUNDS, {
    padding: [20, 20],
    animate: false
  });
}

function resolveCompanyId() {
  const params = new URLSearchParams(window.location.search);
  const fromQuery = params.get("companyId");

  if (fromQuery) return fromQuery;

  const raw = sessionStorage.getItem("icaro_ops_company");
  if (!raw) return null;

  try {
    const parsed = JSON.parse(raw);
    return parsed.company_id || null;
  } catch {
    return null;
  }
}

function renderCompany(company) {
  const airport = company.base_airport;
  document.querySelector("#companySummary").innerHTML = `
    ${summaryRow("Company", company.company_name)}
    ${summaryRow("Budget", `${company.budget_amount} ${company.currency_code}`)}
    ${summaryRow("Reputation", company.reputation_score)}
    ${summaryRow("Base", `${airport.icao_code}${airport.iata_code ? " / " + airport.iata_code : ""}`)}
    ${summaryRow("Airport", airport.airport_name)}
    ${summaryRow("Country", airport.country_name)}
  `;

  renderMarketSummary(airport);
}

function renderMarketSummary(airport) {
  const rows = [
    ["Passengers", airport.local_passenger_demand_score],
    ["Cargo", airport.local_cargo_demand_score],
    ["Tourism", airport.tourism_score],
    ["Business", airport.business_score],
    ["Competition", airport.competition_score],
    ["Airport fees", airport.airport_fee_score],
  ];

  document.querySelector("#marketSummary").innerHTML = rows.map(([label, value]) => metricRow(label, value)).join("");
}

function renderHqMarker(company) {
  hqLayer.clearLayers();

  const airport = company.base_airport;

  if (!airport?.latitude || !airport?.longitude) return;

  const marker = L.marker([Number(airport.latitude), Number(airport.longitude)], {
    icon: L.divIcon({
      className: "",
      html: hqIconSvg("hq-marker"),
      iconSize: [38, 38],
      iconAnchor: [19, 19],
      popupAnchor: [0, -18]
    }),
    title: `${company.company_name} HQ`
  });

  marker.bindPopup(`
    <div class="base-popup">
      <h3>${escapeHtml(company.company_name)} HQ</h3>
      <p><strong>${escapeHtml(airport.icao_code)}${airport.iata_code ? " / " + escapeHtml(airport.iata_code) : ""}</strong></p>
      <p>${escapeHtml(airport.airport_name)}</p>
      <p>${escapeHtml(airport.city || airport.location_name || "")}, ${escapeHtml(airport.country_name)}</p>
      <dl>
        <dt>Difficulty</dt><dd>${escapeHtml(airport.starting_difficulty || "-")}</dd>
        <dt>Passengers</dt><dd>${safeScore(airport.local_passenger_demand_score)}</dd>
        <dt>Cargo</dt><dd>${safeScore(airport.local_cargo_demand_score)}</dd>
        <dt>Fees</dt><dd>${safeScore(airport.airport_fee_score)}</dd>
      </dl>
    </div>
  `);

  marker.addTo(hqLayer);
}

async function renderRivalBases(companyId) {
  rivalLayer.clearLayers();

  try {
    const rivals = await getJson(API.rivalBases(companyId));

    for (const rival of rivals) {
      if (!rival.latitude || !rival.longitude) continue;

      const marker = L.marker([Number(rival.latitude), Number(rival.longitude)], {
        icon: L.divIcon({
          className: "",
          html: hqIconSvg("rival-base-marker"),
          iconSize: [28, 28],
          iconAnchor: [14, 14],
          popupAnchor: [0, -14]
        }),
        title: `${rival.company_name} base`
      });

      marker.bindPopup(`
        <div class="base-popup">
          <h3>${escapeHtml(rival.company_name)}</h3>
          <p><strong>${escapeHtml(rival.icao_code)}</strong> · ${escapeHtml(rival.airport_name)}</p>
          <p>${escapeHtml(rival.city || rival.location_name || "")}, ${escapeHtml(rival.country_name)}</p>
          <dl>
            <dt>Reputation</dt><dd>${escapeHtml(rival.reputation_score ?? "-")}</dd>
            <dt>Market</dt><dd>${escapeHtml(rival.starting_difficulty || "-")}</dd>
          </dl>
        </div>
      `);

      marker.addTo(rivalLayer);
    }
  } catch {
    // Optional for now.
  }
}

function summaryRow(label, value) {
  return `
    <div>
      <dt>${escapeHtml(label)}</dt>
      <dd>${escapeHtml(value ?? "-")}</dd>
    </div>
  `;
}

function metricRow(label, value) {
  const score = Number(value ?? 0);
  const safe = Math.max(0, Math.min(100, score));
  return `
    <div class="metric-row">
      <span>${escapeHtml(label)}</span>
      <strong>${safe}</strong>
      <div class="metric-bar"><i style="--value: ${safe}%"></i></div>
    </div>
  `;
}

function hqIconSvg(className) {
  return `
    <div class="${className}">
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path d="M3 21h18v-2h-1V8.9L12 3 4 8.9V19H3v2Zm4-2v-8h3v8H7Zm5 0v-8h3v8h-3Zm5 0v-8h1v8h-1ZM7.6 8.7 12 5.45l4.4 3.25H7.6Z"/>
      </svg>
    </div>
  `;
}

function airportIconSvg(className) {
  return `
    <div class="${className}">
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path d="M21 16v-2l-8-5V3.5a1.5 1.5 0 0 0-3 0V9l-8 5v2l8-2.5V19l-2 1.5V22l3.5-1 3.5 1v-1.5L13 19v-5.5l8 2.5Z"/>
      </svg>
    </div>
  `;
}

function setCompanySummaryError(message) {
  document.querySelector("#companySummary").innerHTML = `
    <div>
      <dt>Error</dt>
      <dd>${escapeHtml(message)}</dd>
    </div>
  `;
}

function startUtcClock() {
  const clock = document.querySelector("#utcClock");

  function tick() {
    const now = new Date();
    clock.textContent = now.toISOString().replace("T", " ").slice(0, 19) + " UTC";
  }

  tick();
  setInterval(tick, 1000);
}

async function getJson(url) {
  const response = await fetch(url, {
    headers: { "Accept": "application/json" }
  });

  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }

  return response.json();
}

function safeScore(value) {
  return value == null ? "-" : String(value);
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}
