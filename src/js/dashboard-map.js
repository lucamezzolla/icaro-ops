const API = {
  currentCompany: companyId => `api/public/company/current.php?companyId=${encodeURIComponent(companyId)}`,
  rivalBases: companyId => `api/public/rivals/bases.php?companyId=${encodeURIComponent(companyId)}`
};

const DEFAULT_WORLD_CENTER = [20, 10];
const DEFAULT_WORLD_ZOOM = 3;
const MIN_WORLD_ZOOM = 2;

let map;
let hqLayer;
let rivalLayer;

document.addEventListener("DOMContentLoaded", async () => {
  startUtcClock();
  initMap();

  const companyId = resolveCompanyId();

  if (!companyId) {
    setCompanySummaryError("No company found. Create a company first.");
    return;
  }

  await loadDashboard(companyId);
});

function initMap() {
  map = L.map("map", {
    worldCopyJump: true,
    minZoom: MIN_WORLD_ZOOM,
    zoomControl: true
  }).setView(DEFAULT_WORLD_CENTER, DEFAULT_WORLD_ZOOM);

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 18,
    attribution: "&copy; OpenStreetMap contributors"
  }).addTo(map);

  hqLayer = L.layerGroup().addTo(map);
  rivalLayer = L.layerGroup().addTo(map);
}

async function loadDashboard(companyId) {
  try {
    const company = await getJson(API.currentCompany(companyId));
    renderCompany(company);
    renderHqMarker(company);
    await renderRivalBases(companyId);

    const airport = company.base_airport;
    if (airport?.latitude && airport?.longitude) {
      map.setView([Number(airport.latitude), Number(airport.longitude)], 7);
    }
  } catch (error) {
    setCompanySummaryError("Unable to load company. Check API, PHP and MySQL configuration.");
  }
}

function resolveCompanyId() {
  const params = new URLSearchParams(window.location.search);
  const fromQuery = params.get("companyId");

  if (fromQuery) {
    return fromQuery;
  }

  const raw = sessionStorage.getItem("icaro_ops_company");

  if (!raw) {
    return null;
  }

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

  document.querySelector("#marketSummary").innerHTML = rows
    .map(([label, value]) => metricRow(label, value))
    .join("");
}

function renderHqMarker(company) {
  hqLayer.clearLayers();

  const airport = company.base_airport;

  if (!airport?.latitude || !airport?.longitude) {
    return;
  }

  const marker = L.marker(
    [Number(airport.latitude), Number(airport.longitude)],
    {
      icon: L.divIcon({
        className: "",
        html: hqIconSvg("hq-marker"),
        iconSize: [38, 38],
        iconAnchor: [19, 19],
        popupAnchor: [0, -18]
      }),
      title: `${company.company_name} HQ`
    }
  );

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
      if (!rival.latitude || !rival.longitude) {
        continue;
      }

      const marker = L.marker(
        [Number(rival.latitude), Number(rival.longitude)],
        {
          icon: L.divIcon({
            className: "",
            html: hqIconSvg("rival-base-marker"),
            iconSize: [28, 28],
            iconAnchor: [14, 14],
            popupAnchor: [0, -14]
          }),
          title: `${rival.company_name} base`
        }
      );

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
    // Rivals are optional for now.
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
    clock.textContent = now.toISOString().slice(11, 19) + " UTC";
  }

  tick();
  setInterval(tick, 1000);
}

async function getJson(url) {
  const response = await fetch(url, {
    headers: {
      "Accept": "application/json"
    }
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
