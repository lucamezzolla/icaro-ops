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
const ACTIVE_COMPANY_KEY = "icaro_ops_active_company_id";

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
  syncInternalNavLinks();

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

  window.icaroOpsMap = map;

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

    renderVisibleBases(visibleBasesCache, companyId);

    if (showBasesOnMap) {
      fitMapToVisibleBases(visibleBasesCache);
    } else {
      fitWorldSafely();
    }

    if (companyId) {
      const ownBase = visibleBasesCache.find(base =>
        base.base_owner_type === "PLAYER" && String(base.company_id) === String(companyId)
      );

      if (ownBase) {
        persistActiveCompany(ownBase.company_id);
        renderSelectedBase(ownBase);
      } else {
        await loadAndRenderCompanyFallback(companyId);
      }
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
    persistActiveCompany(company.company_id);
    renderCompanyFallback(company);
  } catch {
    setCompanySummaryError("Company not found. Create a company first.");
  }
}

function persistActiveCompany(companyId) {
  if (!companyId) return;

  sessionStorage.setItem(ACTIVE_COMPANY_KEY, String(companyId));

  const raw = sessionStorage.getItem("icaro_ops_company");
  let payload = {};

  if (raw) {
    try {
      payload = JSON.parse(raw);
    } catch {
      payload = {};
    }
  }

  payload.company_id = Number(companyId);
  sessionStorage.setItem("icaro_ops_company", JSON.stringify(payload));
}

function syncInternalNavLinks() {
  const fleetLink = document.querySelector("#fleetNavLink");
  if (fleetLink) {
    fleetLink.href = "fleet.html";
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
  const markerClass = isOwn
    ? "hq-marker"
    : base.base_owner_type === "RIVAL"
      ? "rival-base-marker"
      : "other-player-base-marker";
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
      <p><strong>Budget:</strong> ${formatBudget(base)}</p>
      <p><strong>${escapeHtml(base.icao_code)}${base.iata_code ? " / " + escapeHtml(base.iata_code) : ""}</strong></p>
      <p>${escapeHtml(base.airport_name)}</p>
      <p>${escapeHtml(base.city || base.location_name || "")}, ${escapeHtml(base.country_name)}</p>
      ${base.markerOffsetLabel ? `<p><em>Marker slightly offset because multiple bases share this airport.</em></p>` : ""}
      <dl>
        <dt>Size</dt><dd>${escapeHtml(base.airport_size_tier || "-")}</dd>
        <dt>Base slots</dt><dd>${escapeHtml(base.max_total_bases ?? "-")}</dd>
        <dt>Aircraft</dt><dd>${safeScore(base.aircraft_owned_count)} / ${safeScore(base.max_aircraft_managed)}</dd>
        <dt>At base</dt><dd>${safeScore(base.aircraft_at_base_count)} / ${safeScore(base.max_aircraft_on_ground)}</dd>
        <dt>In flight</dt><dd>${safeScore(base.aircraft_in_flight_count)}</dd>
        <dt>Maintenance</dt><dd>${safeScore(base.aircraft_maintenance_count)}</dd>
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
    ${summaryRow("Selected", base.base_owner_type === "RIVAL" ? "Virtual rival base" : "Player base")}
    ${summaryRow("Owner", base.owner_name)}
    ${summaryRow("Company", base.company_name)}
    ${summaryRow("Budget", formatBudget(base))}
    ${summaryRow("Reputation", base.reputation_score)}
    ${summaryRow("Base", `${base.icao_code}${base.iata_code ? " / " + base.iata_code : ""}`)}
    ${summaryRow("Airport", base.airport_name)}
    ${summaryRow("Country", base.country_name)}
    ${summaryRow("Airport size", base.airport_size_tier)}
    ${summaryRow("Max bases", base.max_total_bases)}
    ${summaryRow("Base managed aircraft", `${base.aircraft_owned_count} / ${base.max_aircraft_managed}`)}
    ${summaryRow("On ground at current base", `${base.aircraft_at_base_count} / ${base.max_aircraft_on_ground}`)}
    ${summaryRow("Company aircraft in flight", base.aircraft_in_flight_count)}
    ${summaryRow("Company aircraft in maintenance", base.aircraft_maintenance_count)}
    ${summaryRow("Free base fleet slots", base.free_managed_aircraft_slots)}
    ${summaryRow("Free base ground slots", freeGroundSlotsFromBase(base))}
  `;

  renderMarketSummary(base);
}

function renderCompanyFallback(company) {
  const airport = company.base_airport;
  const base = {
    ...airport,
    company_name: company.company_name,
    owner_name: company.owner_name,
    budget_amount: company.budget_amount,
    currency_code: company.currency_code,
    reputation_score: company.reputation_score
  };

  document.querySelector("#companySummary").innerHTML = `
    ${summaryRow("Owner", company.owner_name)}
    ${summaryRow("Company", company.company_name)}
    ${summaryRow("Budget", formatBudget(base))}
    ${summaryRow("Reputation", company.reputation_score)}
    ${summaryRow("Base", `${airport.icao_code}${airport.iata_code ? " / " + airport.iata_code : ""}`)}
    ${summaryRow("Airport", airport.airport_name)}
    ${summaryRow("Country", airport.country_name)}
    ${summaryRow("Base managed aircraft", `${airport.aircraft_owned_count} / ${airport.max_aircraft_managed}`)}
    ${summaryRow("On ground at current base", `${airport.aircraft_at_base_count} / ${airport.max_aircraft_on_ground}`)}
    ${summaryRow("Company aircraft in flight", airport.aircraft_in_flight_count)}
    ${summaryRow("Company aircraft in maintenance", airport.aircraft_maintenance_count)}
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

  if (fromQuery) {
    persistActiveCompany(fromQuery);
    return fromQuery;
  }

  const active = sessionStorage.getItem(ACTIVE_COMPANY_KEY);
  if (active) return active;

  const raw = sessionStorage.getItem("icaro_ops_company");
  if (!raw) return null;

  try {
    const parsed = JSON.parse(raw);
    return parsed.company_id || null;
  } catch {
    return null;
  }
}

function formatBudget(base) {
  if (base.budget_amount == null || base.currency_code == null) {
    return "-";
  }

  const value = Number(base.budget_amount ?? 0).toLocaleString("en-US", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  });

  return `${value} ${base.currency_code}`;
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

/*
 * Live dashboard refresh.
 * Keeps the left Company/Base panel updated after flights complete,
 * without forcing a full page reload.
 */
(function setupLiveCompanyPanelRefresh() {
  const REFRESH_MS = 10000;

  document.addEventListener("DOMContentLoaded", () => {
    refreshCompanyPanelLive();
    setInterval(refreshCompanyPanelLive, REFRESH_MS);
  });

  async function refreshCompanyPanelLive() {
    try {
      const response = await fetch("api/public/company/current.php", {
        headers: { "Accept": "application/json" },
        credentials: "same-origin"
      });

      if (!response.ok) {
        return;
      }

      const data = await response.json();
      updateCompanyPanelFromApi(data);
    } catch {
      // Silent: map/dashboard must remain usable even if the API is temporarily unavailable.
    }
  }

  function updateCompanyPanelFromApi(data) {
    const company = data.company || data;
    const base = data.base || data.base_airport || data.airport || {};
    const capacity = data.aircraft_capacity || data.capacity || data.base_capacity || data;

    const budgetAmount = firstDefined(
      company.budget_amount,
      data.budget_amount,
      data.budget
    );

    const currencyCode = firstDefined(
      company.currency_code,
      data.currency_code,
      "EUR"
    );

    const reputation = Number(firstDefined(
      company.reputation_score,
      data.reputation_score,
      data.reputation,
      100
    ));

    if (budgetAmount !== undefined) {
      setPanelValue("Budget", `${moneyLive(budgetAmount)} ${currencyCode}`);
    }

    setPanelValue("Reputation", `${reputation}/100`, reputationClass(reputation));

    setPanelValueIfPresent("Base managed aircraft", formatPair(
      firstDefined(capacity.aircraft_owned_count, data.aircraft_owned_count),
      firstDefined(capacity.max_aircraft_managed, data.max_aircraft_managed)
    ));

    setPanelValueIfPresent("On ground at current base", formatPair(
      firstDefined(capacity.aircraft_at_base_count, data.aircraft_at_base_count),
      firstDefined(capacity.max_aircraft_on_ground, data.max_aircraft_on_ground)
    ));

    setPanelValueIfPresent("Company aircraft in flight", firstDefined(
      data.aircraft_in_flight_count,
      capacity.aircraft_in_flight_count
    ));

    setPanelValueIfPresent("Company aircraft in maintenance", firstDefined(
      data.aircraft_maintenance_count,
      capacity.aircraft_maintenance_count
    ));

    setPanelValueIfPresent("Free base fleet slots", firstDefined(
      capacity.free_managed_aircraft_slots,
      data.free_managed_aircraft_slots
    ));

    setPanelValueIfPresent("Free base ground slots", firstDefined(
      capacity.free_ground_aircraft_slots,
      data.free_ground_aircraft_slots,
      freeGroundSlotsFromCapacity(capacity, data)
    ));
  }

  function setPanelValueIfPresent(label, value, className = "") {
    if (value === undefined || value === null || value === "undefined / undefined") {
      return;
    }

    setPanelValue(label, value, className);
  }

  function setPanelValue(label, value, className = "") {
    const labelKey = normalizeLabel(label);

    const matchingDt = [...document.querySelectorAll("dt")].find(dt => {
      return normalizeLabel(dt.textContent) === labelKey;
    });

    if (!matchingDt) {
      return;
    }

    const dd = matchingDt.parentElement?.querySelector("dd") || matchingDt.nextElementSibling;

    if (!dd) {
      return;
    }

    dd.textContent = String(value);

    if (labelKey === "reputation") {
      dd.classList.remove("reputation-value", "good", "warning", "bad");
      dd.classList.add("reputation-value");

      if (className) {
        dd.classList.add(className);
      }
    }
  }

  function reputationClass(value) {
    return value < 51 ? "bad" : "";
  }

  function formatPair(current, max) {
    if (current === undefined || current === null || max === undefined || max === null) {
      return undefined;
    }

    return `${current} / ${max}`;
  }

  function moneyLive(value) {
    const numeric = Number(value || 0);

    return numeric.toLocaleString("en-US", {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    });
  }

  function firstDefined(...values) {
    return values.find(value => value !== undefined && value !== null);
  }

  function normalizeLabel(value) {
    return String(value || "")
      .trim()
      .toLowerCase()
      .replace(/\s+/g, " ");
  }
})();

/*
 * Reputation formatting guard.
 * Ensures the sidebar always shows reputation as x/100
 * and red when it drops below 51.
 */
(function setupReputationFormattingGuard() {
  document.addEventListener("DOMContentLoaded", () => {
    formatReputationField();
    setInterval(formatReputationField, 2000);
  });

  function formatReputationField() {
    const dt = [...document.querySelectorAll("dt")].find(item => {
      return String(item.textContent || "").trim().toLowerCase() === "reputation";
    });

    if (!dt) {
      return;
    }

    const dd = dt.parentElement?.querySelector("dd") || dt.nextElementSibling;

    if (!dd) {
      return;
    }

    const raw = String(dd.textContent || "").trim();
    const match = raw.match(/\d+/);

    if (!match) {
      return;
    }

    const value = Number(match[0]);

    dd.textContent = `${value}/100`;
    dd.classList.remove("reputation-value", "bad");
    dd.classList.add("reputation-value");

    if (value < 51) {
      dd.classList.add("bad");
    }
  }
})();

/*
 * Live sidebar refresh after flight completion.
 * It refreshes the left Company/Base panel without reloading the page.
 */
(function setupIcaroOpsLiveSidebarRefresh() {
  const REFRESH_MS = 5000;

  document.addEventListener("DOMContentLoaded", () => {
    refreshSidebarCompanyData();
    setInterval(refreshSidebarCompanyData, REFRESH_MS);
  });

  async function refreshSidebarCompanyData() {
    try {
      /*
       * Important:
       * flights/active.php may complete arrived flights as a side effect.
       * So call it before company/current.php.
       */
      await fetch("api/public/flights/active.php", {
        headers: { "Accept": "application/json" },
        credentials: "same-origin"
      }).catch(() => null);

      const response = await fetch("api/public/company/current.php", {
        headers: { "Accept": "application/json" },
        credentials: "same-origin"
      });

      if (!response.ok) {
        return;
      }

      const data = await response.json();
      updateSidebarValues(data);
    } catch {
      // Silent refresh: do not disturb the map if an API is temporarily unavailable.
    }
  }

  function updateSidebarValues(data) {
    const company = data.company || data;
    const base = data.base || data.base_airport || {};
    const capacity = data.aircraft_capacity || data.capacity || data;

    const budget = firstDefined(company.budget_amount, data.budget_amount);
    const currency = firstDefined(company.currency_code, data.currency_code, "EUR");
    const reputation = Number(firstDefined(company.reputation_score, data.reputation_score, 100));

    setValue("Budget", `${formatMoney(budget)} ${currency}`);
    setValue("Reputation", `${reputation}/100`, reputation < 51 ? "bad" : "");

    setValueIfPresent("Base managed aircraft", formatPair(
      firstDefined(capacity.aircraft_owned_count, capacity.aircraft_count, data.aircraft_owned_count),
      firstDefined(capacity.max_aircraft_managed, data.max_aircraft_managed)
    ));

    setValueIfPresent("On ground at current base", formatPair(
      firstDefined(capacity.aircraft_at_base_count, data.aircraft_at_base_count),
      firstDefined(capacity.max_aircraft_on_ground, data.max_aircraft_on_ground)
    ));

    setValueIfPresent("Company aircraft in flight", firstDefined(
      data.aircraft_in_flight_count,
      capacity.aircraft_in_flight_count
    ));

    setValueIfPresent("Company aircraft in maintenance", firstDefined(
      data.aircraft_maintenance_count,
      capacity.aircraft_maintenance_count
    ));

    setValueIfPresent("Free base fleet slots", firstDefined(
      capacity.free_managed_aircraft_slots,
      data.free_managed_aircraft_slots
    ));

    setValueIfPresent("Free base ground slots", firstDefined(
      capacity.free_ground_aircraft_slots,
      data.free_ground_aircraft_slots,
      freeGroundSlotsFromCapacity(capacity, data)
    ));
  }

  function setValueIfPresent(label, value) {
    if (value === undefined || value === null || value === "undefined / undefined") {
      return;
    }

    setValue(label, value);
  }

  function setValue(label, value, stateClass = "") {
    const dt = [...document.querySelectorAll("dt")].find(item => {
      return normalize(item.textContent) === normalize(label);
    });

    if (!dt) {
      return;
    }

    const dd = dt.parentElement?.querySelector("dd") || dt.nextElementSibling;

    if (!dd) {
      return;
    }

    dd.textContent = String(value);

    if (normalize(label) === "reputation") {
      dd.classList.remove("reputation-value", "bad");
      dd.classList.add("reputation-value");

      if (stateClass) {
        dd.classList.add(stateClass);
      }
    }
  }

  function formatPair(left, right) {
    if (left === undefined || left === null || right === undefined || right === null) {
      return undefined;
    }

    return `${left} / ${right}`;
  }

  function formatMoney(value) {
    return Number(value || 0).toLocaleString("en-US", {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    });
  }

  function firstDefined(...values) {
    return values.find(value => value !== undefined && value !== null);
  }

  function normalize(value) {
    return String(value || "").trim().toLowerCase().replace(/\s+/g, " ");
  }
})();

/*
 * Live sidebar refresh after flight completion.
 * It refreshes the left Company/Base panel without reloading the page.
 */
(function setupIcaroOpsLiveSidebarRefresh() {
  const REFRESH_MS = 5000;

  document.addEventListener("DOMContentLoaded", () => {
    refreshSidebarCompanyData();
    setInterval(refreshSidebarCompanyData, REFRESH_MS);
  });

  async function refreshSidebarCompanyData() {
    try {
      /*
       * Important:
       * flights/active.php may complete arrived flights as a side effect.
       * So call it before company/current.php.
       */
      await fetch("api/public/flights/active.php", {
        headers: { "Accept": "application/json" },
        credentials: "same-origin"
      }).catch(() => null);

      const response = await fetch("api/public/company/current.php", {
        headers: { "Accept": "application/json" },
        credentials: "same-origin"
      });

      if (!response.ok) {
        return;
      }

      const data = await response.json();
      updateSidebarValues(data);
    } catch {
      // Silent refresh: do not disturb the map if an API is temporarily unavailable.
    }
  }

  function updateSidebarValues(data) {
    const company = data.company || data;
    const base = data.base || data.base_airport || {};
    const capacity = data.aircraft_capacity || data.capacity || data;

    const budget = firstDefined(company.budget_amount, data.budget_amount);
    const currency = firstDefined(company.currency_code, data.currency_code, "EUR");
    const reputation = Number(firstDefined(company.reputation_score, data.reputation_score, 100));

    setValue("Budget", `${formatMoney(budget)} ${currency}`);
    setValue("Reputation", `${reputation}/100`, reputation < 51 ? "bad" : "");

    setValueIfPresent("Base managed aircraft", formatPair(
      firstDefined(capacity.aircraft_owned_count, capacity.aircraft_count, data.aircraft_owned_count),
      firstDefined(capacity.max_aircraft_managed, data.max_aircraft_managed)
    ));

    setValueIfPresent("On ground at current base", formatPair(
      firstDefined(capacity.aircraft_at_base_count, data.aircraft_at_base_count),
      firstDefined(capacity.max_aircraft_on_ground, data.max_aircraft_on_ground)
    ));

    setValueIfPresent("Company aircraft in flight", firstDefined(
      data.aircraft_in_flight_count,
      capacity.aircraft_in_flight_count
    ));

    setValueIfPresent("Company aircraft in maintenance", firstDefined(
      data.aircraft_maintenance_count,
      capacity.aircraft_maintenance_count
    ));

    setValueIfPresent("Free base fleet slots", firstDefined(
      capacity.free_managed_aircraft_slots,
      data.free_managed_aircraft_slots
    ));

    setValueIfPresent("Free base ground slots", firstDefined(
      capacity.free_ground_aircraft_slots,
      data.free_ground_aircraft_slots,
      freeGroundSlotsFromCapacity(capacity, data)
    ));
  }

  function setValueIfPresent(label, value) {
    if (value === undefined || value === null || value === "undefined / undefined") {
      return;
    }

    setValue(label, value);
  }

  function setValue(label, value, stateClass = "") {
    const dt = [...document.querySelectorAll("dt")].find(item => {
      return normalize(item.textContent) === normalize(label);
    });

    if (!dt) {
      return;
    }

    const dd = dt.parentElement?.querySelector("dd") || dt.nextElementSibling;

    if (!dd) {
      return;
    }

    dd.textContent = String(value);

    if (normalize(label) === "reputation") {
      dd.classList.remove("reputation-value", "bad");
      dd.classList.add("reputation-value");

      if (stateClass) {
        dd.classList.add(stateClass);
      }
    }
  }

  function formatPair(left, right) {
    if (left === undefined || left === null || right === undefined || right === null) {
      return undefined;
    }

    return `${left} / ${right}`;
  }

  function formatMoney(value) {
    return Number(value || 0).toLocaleString("en-US", {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    });
  }

  function firstDefined(...values) {
    return values.find(value => value !== undefined && value !== null);
  }

  function normalize(value) {
    return String(value || "").trim().toLowerCase().replace(/\s+/g, " ");
  }
})();

/*
 * Definitive sidebar refresh using current company API shape.
 * company/current.php returns capacity data inside base_airport.
 */
(function setupDefinitiveCompanySidebarRefresh() {
  const REFRESH_MS = 5000;

  document.addEventListener("DOMContentLoaded", () => {
    refreshCompanySidebar();
    setInterval(refreshCompanySidebar, REFRESH_MS);
  });

  async function refreshCompanySidebar() {
    try {
      await fetch("api/public/flights/active.php", {
        headers: { "Accept": "application/json" },
        credentials: "same-origin"
      }).catch(() => null);

      const response = await fetch("api/public/company/current.php", {
        headers: { "Accept": "application/json" },
        credentials: "same-origin"
      });

      if (!response.ok) {
        return;
      }

      const data = await response.json();
      const base = data.base_airport || {};

      setSidebarValue("Budget", `${formatMoney(data.budget_amount)} ${data.currency_code}`);
      setSidebarValue("Reputation", `${Number(data.reputation_score)}/100`, Number(data.reputation_score) < 51 ? "bad" : "");

      setSidebarValue("Base managed aircraft", `${base.aircraft_owned_count} / ${base.max_aircraft_managed}`);
      setSidebarValue("On ground at current base", `${base.aircraft_at_base_count} / ${base.max_aircraft_on_ground}`);
      setSidebarValue("Company aircraft in flight", base.aircraft_in_flight_count);
      setSidebarValue("Company aircraft in maintenance", base.aircraft_maintenance_count);
      setSidebarValue("Free base fleet slots", base.free_managed_aircraft_slots);
      setSidebarValue("Free base ground slots", freeGroundSlotsFromBase(base));
    } catch {
      // Keep dashboard usable during transient API failures.
    }
  }

  function setSidebarValue(label, value, stateClass = "") {
    if (value === undefined || value === null || String(value).includes("undefined")) {
      return;
    }

    const dt = [...document.querySelectorAll("dt")].find(item => {
      return normalizeLabel(item.textContent) === normalizeLabel(label);
    });

    if (!dt) {
      return;
    }

    const dd = dt.parentElement?.querySelector("dd") || dt.nextElementSibling;

    if (!dd) {
      return;
    }

    dd.textContent = String(value);

    if (normalizeLabel(label) === "reputation") {
      dd.classList.remove("reputation-value", "bad");
      dd.classList.add("reputation-value");

      if (stateClass) {
        dd.classList.add(stateClass);
      }
    }
  }

  function formatMoney(value) {
    return Number(value || 0).toLocaleString("en-US", {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    });
  }

  function normalizeLabel(value) {
    return String(value || "")
      .trim()
      .toLowerCase()
      .replace(/\s+/g, " ");
  }
})();

function freeGroundSlotsFromCapacity(capacity = {}, data = {}) {
  const maxGround = firstDefined(
    capacity.max_aircraft_on_ground,
    data.max_aircraft_on_ground
  );
  const atBase = firstDefined(
    capacity.aircraft_at_base_count,
    data.aircraft_at_base_count
  );

  if (maxGround === undefined || atBase === undefined) {
    return undefined;
  }

  const free = Number(maxGround) - Number(atBase);
  return Number.isFinite(free) ? Math.max(0, free) : undefined;
}

function freeGroundSlotsFromBase(base = {}) {
  if (base.free_ground_aircraft_slots !== undefined && base.free_ground_aircraft_slots !== null && base.free_ground_aircraft_slots !== "") {
    return base.free_ground_aircraft_slots;
  }

  const maxGround = base.max_aircraft_on_ground;
  const atBase = base.aircraft_at_base_count;

  if (maxGround === undefined || maxGround === null || atBase === undefined || atBase === null) {
    return undefined;
  }

  const free = Number(maxGround) - Number(atBase);
  return Number.isFinite(free) ? Math.max(0, free) : undefined;
}
