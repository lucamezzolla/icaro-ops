(() => {
  document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll("[data-logout-button], #logoutButton").forEach(button => {
      if (button.dataset.logoutBound === "true") return;
      button.dataset.logoutBound = "true";
      button.addEventListener("click", async event => {
        event.preventDefault();
        try {
          await fetch("api/public/auth/logout.php", {
            method: "POST",
            headers: { "Accept": "application/json" },
            credentials: "same-origin"
          });
        } catch (error) {
          console.warn("Logout request failed, redirecting anyway.", error);
        }
        window.location.href = "login.html";
      });
    });
  });
})();
