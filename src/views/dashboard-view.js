import { gameState } from "../services/game-state.js";
import { t } from "../services/i18n-service.js";

export function createDashboardView() {
  const airline = gameState.getAirline();

  const root = document.createElement("section");
  root.className = "dashboard";

  root.innerHTML = `
    <nav class="sidebar" aria-label="Main navigation">
      <button class="nav-button active" title="Map">✈</button>
      <button class="nav-button" title="Fleet">▦</button>
      <button class="nav-button" title="Routes">⌁</button>
      <button class="nav-button" title="Staff">◎</button>
      <button class="nav-button" title="Finance">€</button>
    </nav>

    <div class="map-stage">
      <div class="fake-map"></div>
      <div class="route-line"></div>
      <div class="aircraft-marker">✈</div>
      <div class="map-caption">
        <strong>${t("dashboard.mapTitle")}</strong>
        <p>${t("dashboard.mapCopy")}</p>
      </div>
    </div>

    <aside class="right-panel">
      <div class="panel-card">
        <h2>${airline.airlineName}</h2>
        <p>${airline.baseAirport} · ${airline.currency}</p>
      </div>

      <div class="panel-card">
        <h3>${t("dashboard.companyStatus")}</h3>
        <div class="metric-grid">
          <div class="metric">
            <span>${t("dashboard.balance")}</span>
            <strong>${formatMoney(airline.currentBalance, airline.currency)}</strong>
          </div>
          <div class="metric">
            <span>${t("dashboard.reputation")}</span>
            <strong>0%</strong>
          </div>
          <div class="metric">
            <span>${t("dashboard.activeFlights")}</span>
            <strong>0</strong>
          </div>
          <div class="metric">
            <span>${t("dashboard.aircraft")}</span>
            <strong>0</strong>
          </div>
        </div>
      </div>

      <div class="panel-card">
        <h3>${t("dashboard.nextStep")}</h3>
        <p>${t("dashboard.nextStepCopy")}</p>
      </div>
    </aside>
  `;

  return { root };
}

function formatMoney(value, currency) {
  return new Intl.NumberFormat("en", {
    style: "currency",
    currency,
    maximumFractionDigits: 0
  }).format(value);
}
