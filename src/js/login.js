document.addEventListener("DOMContentLoaded", () => {
  const form = document.querySelector("#loginForm");
  const error = document.querySelector("#loginError");

  form.addEventListener("submit", async event => {
    event.preventDefault();

    if (error) {
      error.hidden = true;
      error.textContent = "";
    }

    const payload = {
      email: document.querySelector("#email").value.trim(),
      password: document.querySelector("#password").value
    };

    try {
      const response = await fetch("api/public/auth/login.php", {
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
        throw new Error(body?.message || body?.error || "Login failed.");
      }

      sessionStorage.setItem("icaro_ops_active_company_id", String(body.company_id));
      sessionStorage.setItem("icaro_ops_company", JSON.stringify(body));

      const next = new URLSearchParams(window.location.search).get("next");
      window.location.href = sanitizeNext(next) || "index.html";
    } catch (err) {
      if (error) {
        error.hidden = false;
        error.textContent = err.message || "Login failed.";
      }
    }
  });
});

function sanitizeNext(next) {
  if (!next) return null;

  // Keep navigation local only: no external URLs, no absolute paths.
  if (next.includes("://") || next.startsWith("//") || next.startsWith("/")) {
    return null;
  }

  // Avoid redirect loops.
  if (next.startsWith("login.html")) {
    return null;
  }

  return next;
}
