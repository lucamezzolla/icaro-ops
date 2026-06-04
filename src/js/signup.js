/*
 * Icaro Ops signup page.
 *
 * Supports the Starting base cascade:
 *   Region -> Country -> Airport
 *
 * Expected endpoint family:
 *   api/public/starting-base/regions.php
 *   api/public/starting-base/countries.php?worldRegionCode=EUROPE
 *   api/public/starting-base/countries.php?region=EUROPE
 *   api/public/starting-base/airports.php?countryId=123
 *   api/public/starting-base/airports.php?country_id=123
 *
 * The code is deliberately tolerant about element IDs because the signup page
 * changed a few times during development.
 */

const SIGNUP_API = {
  regions: "api/public/starting-base/regions.php",
  countriesByRegion: regionCode => [
    `api/public/starting-base/countries.php?worldRegionCode=${encodeURIComponent(regionCode)}`,
    `api/public/starting-base/countries.php?region=${encodeURIComponent(regionCode)}`,
    `api/public/starting-base/countries.php?world_region_code=${encodeURIComponent(regionCode)}`
  ],
  airportsByCountry: countryId => [
    `api/public/starting-base/airports.php?countryId=${encodeURIComponent(countryId)}`,
    `api/public/starting-base/airports.php?country_id=${encodeURIComponent(countryId)}`
  ]
};

document.addEventListener("DOMContentLoaded", async () => {
  const form = document.querySelector("#signupForm");
  const regionSelect = findElement("worldRegionCode", "regionSelect", "worldRegionSelect", "startingBaseRegion");
  const countrySelect = findElement("countryId", "countrySelect", "startingBaseCountry");
  const airportSelect = findElement("baseAirportIcao", "baseAirportIcaoCode", "airportSelect", "startingBaseAirport");
  const error = findElement("signupError", "formError");

  await initializeStartingBaseSelectors(regionSelect, countrySelect, airportSelect, error);

  if (form) {
    form.addEventListener("submit", async event => {
      event.preventDefault();
      await submitSignup(form, airportSelect, error);
    });
  }
});

async function initializeStartingBaseSelectors(regionSelect, countrySelect, airportSelect, error) {
  if (!regionSelect || !countrySelect || !airportSelect) {
    showError(error, "Starting base selectors were not found in signup.html.");
    return;
  }

  setSelectLoading(regionSelect, "Loading regions...");
  setSelectDisabled(countrySelect, "Select a region first");
  setSelectDisabled(airportSelect, "Select a country first");

  try {
    const regions = normalizeRows(await getJson(SIGNUP_API.regions));
    fillRegionSelect(regionSelect, regions);
  } catch (err) {
    setSelectDisabled(regionSelect, "Unable to load regions");
    showError(error, `Unable to load starting regions: ${err.message}`);
    return;
  }

  regionSelect.addEventListener("change", async () => {
    const regionCode = regionSelect.value;

    setSelectDisabled(countrySelect, "Loading countries...");
    setSelectDisabled(airportSelect, "Select a country first");

    if (!regionCode) {
      setSelectDisabled(countrySelect, "Select a region first");
      return;
    }

    try {
      const countries = normalizeRows(await getJsonWithFallback(SIGNUP_API.countriesByRegion(regionCode)));
      fillCountrySelect(countrySelect, countries);
    } catch (err) {
      setSelectDisabled(countrySelect, "Unable to load countries");
      showError(error, `Unable to load countries: ${err.message}`);
    }
  });

  countrySelect.addEventListener("change", async () => {
    const countryId = countrySelect.value;

    setSelectDisabled(airportSelect, "Loading airports...");

    if (!countryId) {
      setSelectDisabled(airportSelect, "Select a country first");
      return;
    }

    try {
      const airports = normalizeRows(await getJsonWithFallback(SIGNUP_API.airportsByCountry(countryId)));
      fillAirportSelect(airportSelect, airports);
    } catch (err) {
      setSelectDisabled(airportSelect, "Unable to load airports");
      showError(error, `Unable to load airports: ${err.message}`);
    }
  });
}

async function submitSignup(form, airportSelect, error) {
  hideError(error);

  const payload = {
    first_name: valueOf("firstName", "first_name"),
    last_name: valueOf("lastName", "last_name"),
    email: valueOf("email"),
    password: valueOf("password"),
    company_name: valueOf("companyName", "company_name"),
    interface_language: valueOf("interfaceLanguage", "interface_language") || "it",
    currency_code: valueOf("currencyCode", "currency_code") || "EUR",
    base_airport_icao_code: getAirportIcao(airportSelect)
  };

  try {
    const response = await fetch("api/public/signup.php", {
      method: "POST",
      headers: {
        "Accept": "application/json",
        "Content-Type": "application/json"
      },
      credentials: "same-origin",
      body: JSON.stringify(payload)
    });

    const body = await response.json().catch(() => null);

    if (!response.ok) {
      throw new Error(body?.message || body?.error || "Signup failed.");
    }

    sessionStorage.setItem("icaro_ops_active_company_id", String(body.company_id));
    sessionStorage.setItem("icaro_ops_company", JSON.stringify(body));

    window.location.href = "index.html";
  } catch (err) {
    showError(error, err.message || "Signup failed.");
  }
}

function fillRegionSelect(select, rows) {
  select.disabled = false;
  select.innerHTML = `<option value="">Select region</option>`;

  for (const row of rows) {
    const code = row.code ?? row.world_region_code ?? row.region_code ?? row.id ?? "";
    const name = row.name ?? row.world_region_name ?? row.region_name ?? code;

    if (!code) continue;

    select.appendChild(option(String(code), String(name)));
  }

  if (select.options.length <= 1) {
    setSelectDisabled(select, "No regions available");
  }
}

function fillCountrySelect(select, rows) {
  select.disabled = false;
  select.innerHTML = `<option value="">Select country</option>`;

  for (const row of rows) {
    const id = row.id ?? row.country_id ?? "";
    const name = row.name ?? row.country_name ?? "";

    if (!id || !name) continue;

    select.appendChild(option(String(id), String(name)));
  }

  if (select.options.length <= 1) {
    setSelectDisabled(select, "No countries available");
  }
}

function fillAirportSelect(select, rows) {
  select.disabled = false;
  select.innerHTML = `<option value="">Select airport</option>`;

  for (const row of rows) {
    const icao = row.icao_code ?? row.airport_icao_code ?? row.base_airport_icao_code ?? "";
    const iata = row.iata_code ? ` / ${row.iata_code}` : "";
    const name = row.airport_name ?? row.name ?? "";
    const city = row.city ?? row.location_name ?? "";
    const slots = formatSlots(row);

    if (!icao || !name) continue;

    select.appendChild(option(String(icao), `${icao}${iata} · ${name}${city ? ` · ${city}` : ""}${slots}`));
  }

  if (select.options.length <= 1) {
    setSelectDisabled(select, "No suitable airports available");
  }
}

function formatSlots(row) {
  const free = row.available_total_base_slots ?? row.available_slots ?? null;
  const max = row.max_total_bases ?? null;

  if (free === null || max === null) {
    return "";
  }

  return ` · slots ${free}/${max}`;
}

async function getJson(url) {
  const response = await fetch(url, {
    headers: { "Accept": "application/json" },
    credentials: "same-origin"
  });

  const body = await response.json().catch(() => null);

  if (!response.ok) {
    throw new Error(body?.message || body?.error || `HTTP ${response.status}`);
  }

  return body;
}

async function getJsonWithFallback(urls) {
  let lastError = null;

  for (const url of urls) {
    try {
      return await getJson(url);
    } catch (err) {
      lastError = err;
    }
  }

  throw lastError || new Error("Request failed.");
}

function normalizeRows(payload) {
  if (Array.isArray(payload)) return payload;
  if (Array.isArray(payload?.rows)) return payload.rows;
  if (Array.isArray(payload?.items)) return payload.items;
  if (Array.isArray(payload?.data)) return payload.data;
  if (Array.isArray(payload?.regions)) return payload.regions;
  if (Array.isArray(payload?.countries)) return payload.countries;
  if (Array.isArray(payload?.airports)) return payload.airports;
  return [];
}

function findElement(...ids) {
  for (const id of ids) {
    const element = document.querySelector(`#${id}`);
    if (element) return element;
  }

  return null;
}

function valueOf(...ids) {
  const element = findElement(...ids);
  return String(element?.value ?? "").trim();
}

function getAirportIcao(airportSelect) {
  if (airportSelect) {
    const selected = airportSelect.options[airportSelect.selectedIndex];

    const fromDataset =
      selected?.dataset?.icao ||
      selected?.dataset?.icaoCode ||
      selected?.dataset?.airportIcaoCode;

    if (fromDataset) {
      return String(fromDataset).trim().toUpperCase();
    }

    const value = String(airportSelect.value ?? "").trim().toUpperCase();

    // If the select value is already an ICAO code, use it.
    if (/^[A-Z0-9]{4}$/.test(value)) {
      return value;
    }

    // Fallback: extract the first ICAO-like code from the visible option text.
    // Example: "LIRA / CIA · Rome Ciampino ..."
    const text = String(selected?.textContent ?? "").toUpperCase();
    const match = text.match(/\b[A-Z0-9]{4}\b/);

    if (match) {
      return match[0];
    }
  }

  return valueOf("baseAirportIcao", "baseAirportIcaoCode").toUpperCase();
}

function option(value, label) {
  const option = document.createElement("option");
  option.value = value;
  option.textContent = label;
  return option;
}

function setSelectLoading(select, label) {
  if (!select) return;
  select.disabled = true;
  select.innerHTML = `<option value="">${escapeHtml(label)}</option>`;
}

function setSelectDisabled(select, label) {
  if (!select) return;
  select.disabled = true;
  select.innerHTML = `<option value="">${escapeHtml(label)}</option>`;
}

function showError(error, message) {
  if (!error) {
    console.error(message);
    return;
  }

  error.hidden = false;
  error.textContent = message;
}

function hideError(error) {
  if (!error) return;

  error.hidden = true;
  error.textContent = "";
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}
