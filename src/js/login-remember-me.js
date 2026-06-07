(() => {
  const originalFetch = window.fetch.bind(window);

  window.fetch = (input, init = {}) => {
    const url = typeof input === "string" ? input : String(input?.url || "");
    const method = String(init?.method || "GET").toUpperCase();

    if (method === "POST" && url.includes("login") && init && typeof init.body === "string") {
      try {
        const body = JSON.parse(init.body);
        const checkbox = document.querySelector("#rememberMe, [name='remember_me']");
        body.remember_me = Boolean(checkbox?.checked);
        init = { ...init, body: JSON.stringify(body) };
      } catch (error) {}
    }

    return originalFetch(input, init);
  };
})();
