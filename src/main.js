import { createAppShell } from "./views/app-shell.js";
import { createSetupView } from "./views/setup-view.js";
import { createDashboardView } from "./views/dashboard-view.js";
import { gameState } from "./services/game-state.js";
import { i18n } from "./services/i18n-service.js";

async function bootstrap() {
  await i18n.load("en");

  const app = document.querySelector("#app");
  app.innerHTML = "";

  const shell = createAppShell();
  app.appendChild(shell.root);

  if (!gameState.hasAirline()) {
    shell.setContent(await createSetupView({
      onCompleted: () => {
        shell.setContent(createDashboardView());
      }
    }));
    return;
  }

  shell.setContent(createDashboardView());
}

bootstrap().catch((error) => {
  console.error("Application bootstrap failed:", error);
});
