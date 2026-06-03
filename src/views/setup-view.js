import { gameState } from "../services/game-state.js";
import { t } from "../services/i18n-service.js";
import { loadStarterAirports } from "../services/airport-service.js";

export async function createSetupView({ onCompleted }) {
  const airports = await loadStarterAirports();

  const root = document.createElement("section");
  root.className = "setup-page";

  const airportOptions = airports
    .map((airport) => `<option value="${airport.icao}">${airport.icao} - ${airport.name}, ${airport.city}, ${airport.country}</option>`)
    .join("");

  root.innerHTML = `
    <div class="hero-panel">
      <div class="hero-kicker">${t("setup.kicker")}</div>
      <h1 class="hero-title">${t("setup.title")}</h1>
      <p class="hero-copy">${t("setup.copy")}</p>
    </div>

    <form class="setup-card">
      <h2>${t("setup.formTitle")}</h2>
      <div class="form-grid">
        <div class="field">
          <label for="language">${t("setup.language")}</label>
          <select id="language" name="language">
            <option value="en">English</option>
            <option value="it">Italiano</option>
            <option value="es">Español</option>
            <option value="pt">Português</option>
            <option value="fr">Français</option>
          </select>
        </div>

        <div class="field">
          <label for="currency">${t("setup.currency")}</label>
          <select id="currency" name="currency">
            <option value="EUR">EUR</option>
            <option value="USD">USD</option>
          </select>
        </div>

        <div class="field">
          <label for="nickname">${t("setup.nickname")}</label>
          <input id="nickname" name="nickname" required maxlength="32" placeholder="CloudRaven">
        </div>

        <div class="field">
          <label for="airlineName">${t("setup.airlineName")}</label>
          <input id="airlineName" name="airlineName" required maxlength="64" placeholder="North Ember Air">
        </div>

        <div class="field">
          <label for="baseAirport">${t("setup.baseAirport")}</label>
          <select id="baseAirport" name="baseAirport">
            ${airportOptions}
          </select>
        </div>

        <p class="form-note">${t("setup.zeroBudgetNote")}</p>

        <button class="primary-button" type="submit">${t("setup.start")}</button>
      </div>
    </form>
  `;

  const form = root.querySelector("form");
  form.addEventListener("submit", (event) => {
    event.preventDefault();

    const data = new FormData(form);
    gameState.createAirline({
      language: data.get("language"),
      currency: data.get("currency"),
      nickname: data.get("nickname"),
      airlineName: data.get("airlineName"),
      baseAirport: data.get("baseAirport"),
      currentBalance: 0,
      createdAtUtc: new Date().toISOString()
    });

    onCompleted();
  });

  return { root };
}
