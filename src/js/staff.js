const API = {
  me: "api/public/auth/me.php",
  myStaff: "api/public/staff/my-staff.php",
  candidates: role => `api/public/staff/candidates.php${role ? `?role=${encodeURIComponent(role)}` : ""}`,
  hire: "api/public/staff/hire.php"
};

let currentRoleFilter = "";

document.addEventListener("DOMContentLoaded", async () => {
  startUtcClock();

  document.querySelector("#refreshButton")?.addEventListener("click", loadStaffPage);

  document.querySelectorAll("[data-role-filter]").forEach(button => {
    button.addEventListener("click", async () => {
      currentRoleFilter = button.dataset.roleFilter || "";
      await loadCandidates();
    });
  });

  await loadStaffPage();
});

async function loadStaffPage() {
  hideError();

  try {
    const me = await getJson(API.me);
    renderCompany(me);

    await Promise.all([
      loadMyStaff(),
      loadCandidates()
    ]);
  } catch (error) {
    showError(error.message || "Unable to load staff page.");
  }
}

function renderCompany(me) {
  document.querySelector("#companySummary").innerHTML = `
    ${summaryRow("Owner", me.owner_name)}
    ${summaryRow("Company", me.company_name)}
    ${summaryRow("Budget", `${money(me.budget_amount)} ${me.currency_code}`)}
    ${summaryRow("Base", `${me.base_airport.icao_code}${me.base_airport.iata_code ? " / " + me.base_airport.iata_code : ""}`)}
  `;
}

async function loadMyStaff() {
  const rows = await getJson(API.myStaff);
  const list = document.querySelector("#myStaffList");

  if (!rows.length) {
    list.innerHTML = `<p class="muted">No staff hired yet. Hire at least two pilots before dispatching your Cessna.</p>`;
    return;
  }

  list.innerHTML = rows.map(row => staffCard(row, false)).join("");
}

async function loadCandidates() {
  const rows = await getJson(API.candidates(currentRoleFilter));
  const list = document.querySelector("#candidateList");

  if (!rows.length) {
    list.innerHTML = `<p class="muted">No candidates currently available.</p>`;
    return;
  }

  list.innerHTML = rows.map(row => staffCard(row, true)).join("");

  list.querySelectorAll("[data-hire-candidate]").forEach(button => {
    button.addEventListener("click", async () => {
      const candidateId = Number(button.dataset.hireCandidate);

      if (!confirm("Hire this candidate? The hiring bonus will be paid now.")) {
        return;
      }

      try {
        await postJson(API.hire, { candidate_id: candidateId });
        await loadStaffPage();
      } catch (error) {
        showError(error.message || "Unable to hire candidate.");
      }
    });
  });
}

function staffCard(row, isCandidate) {
  const roleLabel = row.staff_role === "PILOT" ? "Pilot" : "Technician";
  const mainHours = row.staff_role === "PILOT"
    ? `${row.flight_hours_total} flight h`
    : `${row.aircraft_maintenance_hours_total} maint. h`;

  return `
    <article class="staff-card">
      <h3>${escapeHtml(row.display_name)}</h3>
      <div class="badges">
        <span class="badge">${escapeHtml(roleLabel)}</span>
        <span class="badge">${escapeHtml(row.experience_level)}</span>
        <span class="badge">${escapeHtml(mainHours)}</span>
      </div>

      <div class="metrics">
        <div><strong>${row.fear_score}</strong><span>Fear</span></div>
        <div><strong>${row.courage_score}</strong><span>Courage</span></div>
        <div><strong>${row.stress_tolerance_score}</strong><span>Stress</span></div>
        <div><strong>${row.reliability_score}</strong><span>Reliability</span></div>
        <div><strong>${row.discipline_score}</strong><span>Discipline</span></div>
        <div><strong>${row.teamwork_score}</strong><span>Teamwork</span></div>
        <div><strong>${row.ambition_score}</strong><span>Ambition</span></div>
        <div><strong>${row.fatigue_risk_score}</strong><span>Fatigue risk</span></div>
      </div>

      <p class="license-text"><strong>Licenses:</strong> ${escapeHtml(row.licenses_summary || "-")}</p>

      <p>
        <strong>Compensation:</strong>
        ${money(row.salary_per_flight)} ${escapeHtml(row.currency_code)} / flight,
        ${money(row.daily_retainer)} ${escapeHtml(row.currency_code)} / day,
        ${escapeHtml(row.revenue_share_percent)}% revenue share
      </p>

      ${isCandidate ? `<p><strong>Hiring bonus:</strong> ${money(row.hiring_bonus)} ${escapeHtml(row.currency_code)}</p>` : ""}
      ${isCandidate ? `<button type="button" data-hire-candidate="${row.candidate_id}">Hire</button>` : ""}
    </article>
  `;
}

async function getJson(url) {
  const response = await fetch(url, {
    headers: { "Accept": "application/json" },
    credentials: "same-origin"
  });

  const body = await response.json().catch(() => null);

  if (!response.ok) {
    throw new Error(body?.message || body?.error || `Request failed: ${response.status}`);
  }

  return body;
}

async function postJson(url, payload) {
  const response = await fetch(url, {
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
    throw new Error(body?.message || body?.error || `Request failed: ${response.status}`);
  }

  return body;
}

function summaryRow(label, value) {
  return `
    <div>
      <dt>${escapeHtml(label)}</dt>
      <dd>${escapeHtml(value ?? "-")}</dd>
    </div>
  `;
}

function startUtcClock() {
  const clock = document.querySelector("#utcClock");

  function tick() {
    const now = new Date();
    clock.textContent = now.toISOString().replace("T", " ").slice(0, 19) + " UTC";
  }

  tick();
  setInterval(tick, 1000);
}

function money(value) {
  const numeric = Number(value ?? 0);
  return numeric.toLocaleString("en-US", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  });
}

function showError(message) {
  const error = document.querySelector("#pageError");
  error.hidden = false;
  error.textContent = message;
}

function hideError() {
  const error = document.querySelector("#pageError");
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
