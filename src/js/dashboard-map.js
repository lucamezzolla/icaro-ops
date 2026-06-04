const API = {
  currentCompany: companyId => `api/public/company/current.php?companyId=${encodeURIComponent(companyId)}`,
  visibleBases: "api/public/map/bases.php",
  airportSearch: query => `api/public/airports/search.php?q=${encodeURIComponent(query)}`
};

const DEFAULT_WORLD_BOUNDS = L.latLngBounds(
  L.latLng(-58, -170),
  L.latLng(76, 170)
);

const SAME_AIRPORT_MARKER_OFFSET_METERS = 180;
const SETTINGS_SHOW_BASES_KEY = "icaro_ops_show_bases_on_map";

let map;
let baseLayer;
let searchLayer;
let currentCompanyId = null;
let visibleBasesCache = [];
let showBasesOnMap = true;

document.addEventListener("DOMContentLoaded", async () => {
  startUtcClock();
  initSettingsState();
  initMap();
  bindAirportSearch();
  bindSettingsPanel();

  currentCompanyId = resolveCompanyId();

  await loadOperationsMap(currentCompanyId);
});

function initSettingsState() {
  const stored = localStorage.getItem(SETTINGS_SHOW_BASES_KEY);
  showBasesOnMap = stored === null ? true : stored === "true";
}

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

  baseLayer = L.layerGroup();
  searchLayer = L.layerGroup().addTo(map);

  if (showBasesOnMap) {
    baseLayer.addTo(map);
  }

  fitWorldSafely();

  window.addEventListener("resize", () => {
    map.invalidateSize({ animate: false });
  });

  requestAnimationFrame(() => map.invalidateSize({ animate: false }));
  setTimeout(() => map.invalidateSize({ animate: false }), 150);
  setTimeout(() => map.invalidateSize({ animate: false }), 500);
  setTimeout(() => map.invalidateSize({ animate: false }), 1000);
}

async function loadOperationsMap(companyId) {
  try {
    visibleBasesCache = await getJson(API.visibleBases);
    const ownBase = companyId ? visibleBasesCache.find(base =>
      base.base_owner_type === "PLAYER" && String(base.company_id) === String(companyId)
    ) || null : null;

    renderVisibleBases(visibleBasesCache, companyId);

    if (showBasesOnMap) {
      fitMapToVisibleBases(visibleBasesCache);
    } else {
      fitWorldSafely();
    }

    if (ownBase) {
      renderSelectedBase(ownBase);
    } else if (companyId) {
      await loadAndRenderCompanyFallback(companyId);
    } else if (visibleBasesCache.length > 0) {
      renderSelectedBase(visibleBasesCache[0]);
    } else {
      setCompanySummaryError("No visible bases yet. Create a company first.");
    }

  } catch (error) {
    setCompanySummaryError("Unable to load visible bases. Check API, PHP and MySQL configuration.");
    fitWorldSafely();
  }
}

async function loadAndRenderCompanyFallback(companyId) {
  try {
    const company = await getJson(API.currentCompany(companyId));
    renderCompanyFallback(company);
  } catch {
    setCompanySummaryError("Company not found. Create a company first.");
  }
}


function bindSettingsPanel() {
  const settingsLink = document.querySelector("#settingsNavLink");
  const settingsPanel = document.querySelector("#settingsPanel");
  const closeSettingsButton = document.querySelector("#closeSettingsButton");
  const showBasesToggle = document.querySelector("#showBasesToggle");

  if (!settingsLink || !settingsPanel || !showBasesToggle) {
    return;
  }

  showBasesToggle.checked = showBasesOnMap;

  settingsLink.addEventListener("click", event => {
    event.preventDefault();
    settingsPanel.hidden = !settingsPanel.hidden;
  });

  if (closeSettingsButton) {
    closeSettingsButton.addEventListener("click", () => {
      settingsPanel.hidden = true;
    });
  }

  showBasesToggle.addEventListener("change", () => {
    showBasesOnMap = showBasesToggle.checked;
    localStorage.setItem(SETTINGS_SHOW_BASES_KEY, String(showBasesOnMap));

    applyBaseLayerVisibility();

    if (showBasesOnMap && visibleBasesCache.length > 0) {
      fitMapToVisibleBases(visibleBasesCache);
    }
  });
}

function applyBaseLayerVisibility() {
  if (!baseLayer || !map) {
    return;
  }

  if (showBasesOnMap) {
    if (!map.hasLayer(baseLayer)) {
      baseLayer.addTo(map);
    }
  } else if (map.hasLayer(baseLayer)) {
    map.removeLayer(baseLayer);
  }
}

function renderVisibleBases(bases, companyId) {
  baseLayer.clearLayers();

  const basesByAirport = groupBasesByAirport(bases);

  for (const airportBases of basesByAirport.values()) {
    const positionedBases = calculateBaseMarkerPositions(airportBases);

    for (const base of positionedBases) {
      renderBaseMarker(base, companyId);
    }
  }

  applyBaseLayerVisibility();
}

function groupBasesByAirport(bases) {
  const mapByAirport = new Map();

  for (const base of bases) {
    if (!base.latitude || !base.longitude) {
      continue;
    }

    const key = base.icao_code || `${base.latitude},${base.longitude}`;

    if (!mapByAirport.has(key)) {
      mapByAirport.set(key, []);
    }

    mapByAirport.get(key).push({
      ...base,
      latitude: Number(base.latitude),
      longitude: Number(base.longitude)
    });
  }

  return mapByAirport;
}

function calculateBaseMarkerPositions(bases) {
  if (bases.length <= 1) {
    return bases.map(base => ({
      ...base,
      markerLatitude: base.latitude,
      markerLongitude: base.longitude,
      markerOffsetLabel: null
    }));
  }

  const count = bases.length;
  const angleStep = (Math.PI * 2) / count;

  return bases.map((base, index) => {
    const startAngle = -Math.PI / 2;
    const angle = startAngle + index * angleStep;
    const offset = offsetLatLng(base.latitude, base.longitude, SAME_AIRPORT_MARKER_OFFSET_METERS, angle);

    return {
      ...base,
      markerLatitude: offset.latitude,
      markerLongitude: offset.longitude,
      markerOffsetLabel: `same airport marker ${index + 1}/${count}`
    };
  });
}

function offsetLatLng(latitude, longitude, meters, angleRadians) {
  const earthRadiusMeters = 6378137;
  const deltaLat = (meters * Math.sin(angleRadians)) / earthRadiusMeters;
  const deltaLng = (meters * Math.cos(angleRadians)) / (earthRadiusMeters * Math.cos(latitude * Math.PI / 180));

  return {
    latitude: latitude + deltaLat * 180 / Math.PI,
    longitude: longitude + deltaLng * 180 / Math.PI
  };
}

function renderBaseMarker(base, companyId) {
  const isOwn = base.base_owner_type === "PLAYER" && String(base.company_id) === String(companyId);
  const markerClass = isOwn ? "hq-marker" : base.base_owner_type === "RIVAL" ? "rival-base-marker" : "other-player-base-marker";
  const title = isOwn ? `${base.company_name} HQ` : `${base.company_name} base`;

  const marker = L.marker([base.markerLatitude, base.markerLongitude], {
    icon: L.divIcon({
      className: "",
      html: hqIconSvg(markerClass),
      iconSize: [38, 38],
      iconAnchor: [19, 19],
      popupAnchor: [0, -18]
    }),
    title
  });

  marker.bindPopup(buildBasePopup(base, isOwn));

  marker.on("click", () => {
    renderSelectedBase(base);
  });

  marker.addTo(baseLayer);
}

function buildBasePopup(base, isOwn) {
  const typeLabel = isOwn ? "Your HQ" : base.base_owner_type === "RIVAL" ? "Virtual rival" : "Player company";

  return `
    <div class="base-popup">
      <h3>${escapeHtml(base.company_name)} ${isOwn ? "HQ" : "Base"}</h3>
      <p><strong>Type:</strong> ${escapeHtml(typeLabel)}</p>
      <p><strong>Owner:</strong> ${escapeHtml(base.owner_name || "-")}</p>
      <p><strong>${escapeHtml(base.icao_code)}${base.iata_code ? " / " + escapeHtml(base.iata_code) : ""}</strong></p>
      <p>${escapeHtml(base.airport_name)}</p>
      <p>${escapeHtml(base.city || base.location_name || "")}, ${escapeHtml(base.country_name)}</p>
      ${base.markerOffsetLabel ? `<p><em>Marker slightly offset because multiple bases share this airport.</em></p>` : ""}
      <dl>
        <dt>Size</dt><dd>${escapeHtml(base.airport_size_tier || "-")}</dd>
        <dt>Base slots</dt><dd>${escapeHtml(base.max_total_bases ?? "-")}</dd>
        <dt>Difficulty</dt><dd>${escapeHtml(base.starting_difficulty || "-")}</dd>
        <dt>Passenger potential</dt><dd>${safeScore(base.local_passenger_demand_score)}</dd>
        <dt>Cargo potential</dt><dd>${safeScore(base.local_cargo_demand_score)}</dd>
      </dl>
    </div>
  `;
}

function fitMapToVisibleBases(bases) {
  const points = bases
    .filter(base => base.latitude && base.longitude)
    .map(base => [Number(base.latitude), Number(base.longitude)]);

  map.invalidateSize({ animate: false });

  if (points.length === 0) {
    fitWorldSafely();
    return;
  }

  if (points.length === 1) {
    map.setView(points[0], 8);
    return;
  }

  const bounds = L.latLngBounds(points);
  map.fitBounds(bounds, {
    padding: [90, 90],
    maxZoom: 9,
    animate: false
  });
}

function renderSelectedBase(base) {
  document.querySelector("#companySummary").innerHTML = `
    ${summaryRow("Selected", base.base_owner_type === "RIVAL" ? "Virtual rival base" : base.base_owner_type === "PLAYER" ? "Player base" : "Base")}
    ${summaryRow("Owner", base.owner_name)}
    ${summaryRow("Company", base.company_name)}
    ${summaryRow("Reputation", base.reputation_score)}
    ${base.currency_code ? summaryRow("Budget", `${base.budget_amount} ${base.currency_code}`) : ""}
    ${summaryRow("Base", `${base.icao_code}${base.iata_code ? " / " + base.iata_code : ""}`)}
    ${summaryRow("Airport", base.airport_name)}
    ${summaryRow("Country", base.country_name)}
    ${summaryRow("Airport size", base.airport_size_tier)}
    ${summaryRow("Max bases", base.max_total_bases)}
  `;

  renderMarketSummary(base);
}

function renderCompanyFallback(company) {
  const airport = company.base_airport;

  document.querySelector("#companySummary").innerHTML = `
    ${summaryRow("Owner", company.owner_name)}
    ${summaryRow("Company", company.company_name)}
    ${summaryRow("Budget", `${company.budget_amount} ${company.currency_code}`)}
    ${summaryRow("Reputation", company.reputation_score)}
    ${summaryRow("Base", `${airport.icao_code}${airport.iata_code ? " / " + airport.iata_code : ""}`)}
    ${summaryRow("Airport", airport.airport_name)}
    ${summaryRow("Country", airport.country_name)}
  `;

  renderMarketSummary(airport);
}

function renderMarketSummary(base) {
  const rows = [
    ["Passenger potential", base.local_passenger_demand_score],
    ["Cargo potential", base.local_cargo_demand_score],
    ["Tourism potential", base.tourism_score],
    ["Business potential", base.business_score],
    ["Competition pressure", base.competition_score],
    ["Airport fees level", base.airport_fee_score],
  ];

  document.querySelector("#marketSummary").innerHTML = rows.map(([label, value]) => metricRow(label, value)).join("");
}

function bindAirportSearch() {
  const form = document.querySelector("#airportSearchForm");
  const input = document.querySelector("#airportSearchInput");
  const results = document.querySelector("#airportSearchResults");

  if (!form || !input || !results) return;

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
