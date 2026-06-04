/*
 * Icaro Ops auth guard.
 *
 * Include this script in protected pages before their page-specific JS:
 *
 *   <script src="src/js/auth-guard.js"></script>
 *
 * It checks the PHP session through api/public/auth/me.php.
 * If no valid session exists, it redirects to login.html.
 */

const ICARO_AUTH = {
  activeCompanyKey: "icaro_ops_active_company_id",
  companyKey: "icaro_ops_company",
  meEndpoint: "api/public/auth/me.php",
  loginPage: "login.html"
};

window.IcaroAuth = {
  requireSession,
  getCurrentSession: () => window.__icaroCurrentSession || null
};

document.addEventListener("DOMContentLoaded", async () => {
  await requireSession();
});

async function requireSession() {
  try {
    const session = await fetchCurrentSession();
    storeCurrentSession(session);
    return session;
  } catch {
    clearLocalSession();
    redirectToLogin();
    return null;
  }
}

async function fetchCurrentSession() {
  const response = await fetch(ICARO_AUTH.meEndpoint, {
    method: "GET",
    headers: {
      "Accept": "application/json"
    },
    credentials: "same-origin"
  });

  const body = await response.json().catch(() => null);

  if (!response.ok) {
    throw new Error(body?.error || "UNAUTHENTICATED");
  }

  return body;
}

function storeCurrentSession(session) {
  window.__icaroCurrentSession = session;

  if (session?.company_id) {
    sessionStorage.setItem(ICARO_AUTH.activeCompanyKey, String(session.company_id));
    sessionStorage.setItem(ICARO_AUTH.companyKey, JSON.stringify(session));
  }
}

function clearLocalSession() {
  window.__icaroCurrentSession = null;
  sessionStorage.removeItem(ICARO_AUTH.activeCompanyKey);
  sessionStorage.removeItem(ICARO_AUTH.companyKey);
}

function redirectToLogin() {
  const current = window.location.pathname.split("/").pop() + window.location.search + window.location.hash;
  const next = current && current !== "login.html" ? `?next=${encodeURIComponent(current)}` : "";
  window.location.replace(`${ICARO_AUTH.loginPage}${next}`);
}
