const SETTINGS = {
  showBasesStorageKey: "icaroOps.showBasesOnMap",
  resetConfirmation: "RESET_MY_ICARO_OPS_DATA"
};

document.addEventListener("DOMContentLoaded", () => {
  startUtcClock();
  initMapSettings();
  initDevReset();
});

function initMapSettings() {
  const toggle = document.querySelector("#showBasesToggle");
  if (!toggle) {
    return;
  }

  const current = localStorage.getItem(SETTINGS.showBasesStorageKey);
  toggle.checked = current === null ? true : current === "true";

  toggle.addEventListener("change", () => {
    localStorage.setItem(SETTINGS.showBasesStorageKey, String(toggle.checked));
    showSuccess("Map preference saved.");
  });
}

function initDevReset() {
  const input = document.querySelector("#resetConfirmInput");
  const button = document.querySelector("#resetAccountButton");

  if (!input || !button) {
    return;
  }

  input.addEventListener("input", () => {
    button.disabled = input.value !== SETTINGS.resetConfirmation;
  });

  button.addEventListener("click", async () => {
    hideMessages();

    if (input.value !== SETTINGS.resetConfirmation) {
      showError("Confirmation text does not match.");
      return;
    }

    const firstConfirm = confirm(
      "This will permanently delete your local development player, company and all related game data. Continue?"
    );

    if (!firstConfirm) {
      return;
    }

    const secondConfirm = confirm(
      "Last confirmation: after reset you will be logged out and redirected to signup. Delete everything?"
    );

    if (!secondConfirm) {
      return;
    }

    button.disabled = true;

    try {
      const response = await fetch("api/public/dev/reset-my-data.php", {
        method: "POST",
        headers: {
          "Accept": "application/json",
          "Content-Type": "application/json"
        },
        credentials: "same-origin",
        body: JSON.stringify({
          confirm: SETTINGS.resetConfirmation
        })
      });

      const body = await response.json().catch(() => null);

      if (!response.ok) {
        throw new Error(body?.message || body?.error || `Reset failed: ${response.status}`);
      }

      showSuccess("Development account reset completed. Redirecting to signup...");

      setTimeout(() => {
        window.location.href = body?.next || "signup.html";
      }, 900);
    } catch (error) {
      button.disabled = false;
      showError(error.message || "Unable to reset development account.");
    }
  });
}

function startUtcClock() {
  const clock = document.querySelector("#utcClock");

  function tick() {
    clock.textContent = new Date().toISOString().replace("T", " ").slice(0, 19) + " UTC";
  }

  tick();
  setInterval(tick, 1000);
}

function showError(message) {
  const error = document.querySelector("#pageError");
  const success = document.querySelector("#pageSuccess");

  if (success) {
    success.hidden = true;
    success.textContent = "";
  }

  if (error) {
    error.hidden = false;
    error.textContent = message;
  }
}

function showSuccess(message) {
  const error = document.querySelector("#pageError");
  const success = document.querySelector("#pageSuccess");

  if (error) {
    error.hidden = true;
    error.textContent = "";
  }

  if (success) {
    success.hidden = false;
    success.textContent = message;
  }
}

function hideMessages() {
  const error = document.querySelector("#pageError");
  const success = document.querySelector("#pageSuccess");

  if (error) {
    error.hidden = true;
    error.textContent = "";
  }

  if (success) {
    success.hidden = true;
    success.textContent = "";
  }
}
