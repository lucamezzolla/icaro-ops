const API = {
  regions: "api/public/starting-base/regions.php",
  countries: regionCode => `api/public/starting-base/countries.php?region=${encodeURIComponent(regionCode)}`,
  airports: countryId => `api/public/starting-base/airports.php?countryId=${encodeURIComponent(countryId)}`,
  signup: "api/public/signup.php"
};

const state = {
  selectedAirport: null
};

const $ = selector => document.querySelector(selector);

const regionSelect = $("#regionSelect");
const countrySelect = $("#countrySelect");
const airportSelect = $("#airportSelect");
const marketPreview = $("#marketPreview");
const formError = $("#formError");
const signupForm = $("#signupForm");

document.addEventListener("DOMContentLoaded", init);

async function init() {
  bindEvents();
  await loadRegions();
}

function bindEvents() {
  regionSelect.addEventListener("change", async () => {
    resetSelect(countrySelect, "Loading countries...");
    resetSelect(airportSelect, "Choose a country first", true);
    renderEmptyPreview();

    if (!regionSelect.value) {
      resetSelect(countrySelect, "Choose a region first", true);
      return;
    }

    await loadCountries(regionSelect.value);
  });

  countrySelect.addEventListener("change", async () => {
    resetSelect(airportSelect, "Loading airports...");
    renderEmptyPreview();

    if (!countrySelect.value) {
      resetSelect(airportSelect, "Choose a country first", true);
      return;
    }

    await loadAirports(countrySelect.value);
  });

  airportSelect.addEventListener("change", () => {
    const option = airportSelect.selectedOptions[0];
    const raw = option?.dataset.airport;

    state.selectedAirport = raw ? JSON.parse(raw) : null;
    renderMarketPreview(state.selectedAirport);
  });

  signupForm.addEventListener("submit", submitSignup);
}

async function loadRegions() {
  try {
    const regions = await getJson(API.regions);
    fillSelect(regionSelect, "Choose a region", regions, region => ({
      value: region.world_region_code,
      label: region.world_region_name
    }));
  } catch (error) {
    showError("Cannot load regions. Check PHP server and database configuration.");
    resetSelect(regionSelect, "API not available", true);
  }
}

async function loadCountries(regionCode) {
  try {
    const countries = await getJson(API.countries(regionCode));
    fillSelect(countrySelect, "Choose a country", countries, country => ({
      value: country.country_id,
      label: country.country_name
    }));
  } catch (error) {
    showError("Cannot load countries for the selected region.");
    resetSelect(countrySelect, "API not available", true);
  }
}

async function loadAirports(countryId) {
  try {
    const airports = await getJson(API.airports(countryId));
    fillSelect(airportSelect, "Choose a starting airport", airports, airport => ({
      value: airport.icao_code,
      label: formatAirportOption(airport),
      data: airport
    }));
  } catch (error) {
    showError("Cannot load starting airports for the selected country.");
    resetSelect(airportSelect, "API not available", true);
  }
}

function fillSelect(select, placeholder, rows, mapper) {
  select.innerHTML = "";
  select.disabled = false;

  const first = document.createElement("option");
  first.value = "";
  first.textContent = placeholder;
  select.appendChild(first);

  for (const row of rows) {
    const mapped = mapper(row);
    const option = document.createElement("option");
    option.value = mapped.value;
    option.textContent = mapped.label;

    if (mapped.data) {
      option.dataset.airport = JSON.stringify(mapped.data);
    }

    select.appendChild(option);
  }

  if (!rows.length) {
    resetSelect(select, "No values available", true);
  }
}

function resetSelect(select, placeholder, disabled = false) {
  select.innerHTML = "";
  const option = document.createElement("option");
  option.value = "";
  option.textContent = placeholder;
  select.appendChild(option);
  select.disabled = disabled;
}

function formatAirportOption(airport) {
  const iata = airport.iata_code ? ` / ${airport.iata_code}` : "";
  const city = airport.city ? ` - ${airport.city}` : "";
  const score = airport.starting_base_score != null ? ` · score ${airport.starting_base_score}` : "";
  return `${airport.icao_code}${iata} · ${airport.airport_name}${city}${score}`;
}

function renderEmptyPreview() {
  state.selectedAirport = null;
  marketPreview.className = "market-preview empty";
  marketPreview.innerHTML = `
    <h3>No airport selected</h3>
    <p>Choose a starting airport to see local demand, costs and difficulty.</p>
  `;
}

function renderMarketPreview(airport) {
  if (!airport) {
    renderEmptyPreview();
    return;
  }

  marketPreview.className = "market-preview";
  marketPreview.innerHTML = `
    <h3>${escapeHtml(airport.airport_name)}</h3>
    <p>
      ${escapeHtml(airport.icao_code)}${airport.iata_code ? " / " + escapeHtml(airport.iata_code) : ""}
      · ${escapeHtml(airport.city || airport.location_name || "Unknown location")}
      · ${escapeHtml(airport.base_tier || "Base")}
      · ${escapeHtml(airport.starting_difficulty || "MEDIUM")}
    </p>

    <div class="market-grid">
      ${metric("Passengers", airport.local_passenger_demand_score)}
      ${metric("Cargo", airport.local_cargo_demand_score)}
      ${metric("Tourism", airport.tourism_score)}
      ${metric("Business", airport.business_score)}
      ${metric("Competition", airport.competition_score)}
      ${metric("Airport fees", airport.airport_fee_score)}
    </div>
  `;
}

function metric(label, value) {
  const safeValue = value == null ? "-" : value;
  return `
    <div class="market-metric">
      <strong>${safeValue}</strong>
      <span>${escapeHtml(label)}</span>
    </div>
  `;
}

async function submitSignup(event) {
  event.preventDefault();
  hideError();

  if (!state.selectedAirport) {
    showError("Choose a valid starting airport before creating the company.");
    return;
  }

  const payload = {
    nickname: $("#nickname").value.trim(),
    company_name: $("#companyName").value.trim(),
    interface_language: $("#interfaceLanguage").value,
    currency_code: $("#currencyCode").value,
    base_airport_icao_code: state.selectedAirport.icao_code
  };

  try {
    const response = await fetch(API.signup, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(payload)
    });

    const body = await response.json().catch(() => ({}));

    if (!response.ok) {
      throw new Error(body.message || `Signup failed with status ${response.status}`);
    }

    sessionStorage.setItem("icaro_ops_company", JSON.stringify(body));
    window.location.href = "index.html";
  } catch (error) {
    showError(error.message || "Unable to create company.");
  }
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

function showError(message) {
  formError.hidden = false;
  formError.textContent = message;
}

function hideError() {
  formError.hidden = true;
  formError.textContent = "";
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}
