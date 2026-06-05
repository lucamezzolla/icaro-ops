const API = {
  list: "api/public/staff/list.php",
  candidates: "api/public/staff/candidates.php",
  hire: "api/public/staff/hire.php",
  detail: id => `api/public/staff/detail.php?staffId=${encodeURIComponent(id)}`
};

let staffRows = [];

document.addEventListener("DOMContentLoaded", async () => {
  startUtcClock();
  document.querySelector("#refreshButton")?.addEventListener("click", loadStaff);
  document.querySelector("#addStaffButton")?.addEventListener("click", openAddStaffDialog);
  await loadStaff();
});

async function loadStaff() {
  hideError();
  try {
    const data = await getJson(API.list);
    staffRows = Array.isArray(data) ? data : (data.staff || data.rows || []);
    renderSummary(staffRows);
    renderStaff(staffRows);
  } catch (error) {
    showError(error.message || "Unable to load staff.");
  }
}

function renderSummary(rows) {
  const pilots = rows.filter(s => s.staff_role === "PILOT").length;
  const techs = rows.filter(s => s.staff_role === "TECHNICIAN").length;
  document.querySelector("#staffSummary").innerHTML = `
    ${summaryRow("Total", rows.length)}
    ${summaryRow("Pilots", pilots)}
    ${summaryRow("Techs", techs)}
  `;
}

function renderStaff(rows) {
  const tbody = document.querySelector("#staffTableBody");
  if (!rows.length) {
    tbody.innerHTML = `<tr><td colspan="7">No staff hired yet.</td></tr>`;
    return;
  }

  tbody.innerHTML = rows.map(s => `
    <tr>
      <td><strong>${escapeHtml(s.display_name || s.full_name || "-")}</strong></td>
      <td>${escapeHtml(s.staff_role || "-")}</td>
      <td><span class="badge ${s.employment_status === "ACTIVE" ? "good" : "warn"}">${escapeHtml(s.employment_status || "-")}</span></td>
      <td>${escapeHtml(s.reliability_score ?? "-")}</td>
      <td>${escapeHtml(s.fatigue_score ?? "-")}</td>
      <td>${staffCostProfile(s)}</td>
      <td><button type="button" data-staff-detail="${s.company_staff_id || s.staff_id || s.id}">Details</button></td>
    </tr>
  `).join("");

  tbody.querySelectorAll("[data-staff-detail]").forEach(button => {
    button.addEventListener("click", () => openStaffDetail(Number(button.dataset.staffDetail)));
  });
}

async function openStaffDetail(staffId) {
  const dialog = document.querySelector("#staffDetailDialog");
  const title = document.querySelector("#staffDetailTitle");
  const content = document.querySelector("#staffDetailContent");
  title.textContent = "Staff member";
  content.textContent = "Loading...";
  dialog.showModal();

  try {
    const data = await getJson(API.detail(staffId));
    const staff = data.staff || data;
    const licenses = data.licenses || [];
    title.textContent = staff.display_name || staff.full_name || "Staff member";
    content.innerHTML = `
      <div class="detail-grid">
        ${section("Identity", [
          ["Name", staff.display_name || staff.full_name],
          ["Role", staff.staff_role],
          ["Status", staff.employment_status],
          ["Hired at UTC", staff.hired_at_utc || staff.created_at_utc]
        ])}
        ${section("Personality", [
          ["Reliability", staff.reliability_score],
          ["Fatigue", staff.fatigue_score],
          ["Courage", staff.courage_score],
          ["Fear", staff.fear_score],
          ["Stress", staff.stress_score]
        ])}
        ${section("Compensation", [
          ["Indicative leg fee", `${money(staff.salary_per_flight)} ${staff.currency_code || "EUR"}`],
          ["Revenue share estimate", `${staff.revenue_share_percent || 0}%`]
        ])}
        <section class="detail-section">
          <h3>Licenses</h3>
          ${
            licenses.length
              ? `<dl class="detail-list">${licenses.map(l => `
                ${detailRow("Code", l.license_code || l.code)}
                ${detailRow("Name", l.license_name || l.name || "-")}
              `).join("")}</dl>`
              : `<p class="muted">No licenses found.</p>`
          }
        </section>
      </div>
    `;
  } catch (error) {
    content.innerHTML = `<div class="page-error">${escapeHtml(error.message || "Unable to load staff detail.")}</div>`;
  }
}

async function openAddStaffDialog() {
  const dialog = document.querySelector("#addStaffDialog");
  const list = document.querySelector("#candidateList");
  list.innerHTML = `
    <div class="info-box staff-policy-box">
      <strong>Operational staffing policy</strong>
      <p>2 active qualified pilots are required for each operational aircraft.</p>
      <p>Recommended maintenance coverage: 1 qualified technician every 3 aircraft.</p>
      <p>Candidate costs are indicative estimates and may evolve with contracts, experience, fatigue, morale and company policy.</p>
    </div>
    <p class="muted">Loading candidates...</p>
  `;
  dialog.showModal();

  try {
    const data = await getJson(API.candidates);
    const candidates = Array.isArray(data) ? data : (data.candidates || data.rows || []);
    if (!candidates.length) {
      list.innerHTML = `<p class="muted">No candidates available right now.</p>`;
      return;
    }
    list.innerHTML = candidates.map(c => `
      <article class="candidate-card">
        <div>
          <strong>${escapeHtml(c.display_name || c.full_name || "-")}</strong>
          <p class="muted">
            ${escapeHtml(c.staff_role || "-")} · Reliability ${escapeHtml(c.reliability_score ?? "-")} ·
            Indicative cost: ${candidateCostProfile(c)}
          </p>
          <p class="muted">Licenses: ${escapeHtml(c.licenses || "-")}</p>
        </div>
        <button type="button" data-hire-candidate="${c.candidate_id || c.id}">Hire</button>
      </article>
    `).join("");

    list.querySelectorAll("[data-hire-candidate]").forEach(button => {
      button.addEventListener("click", async () => {
        try {
          await postJson(API.hire, { candidate_id: Number(button.dataset.hireCandidate) });
          dialog.close();
          await loadStaff();
        } catch (error) {
          alert(error.message || "Unable to hire candidate.");
        }
      });
    });
  } catch (error) {
    list.innerHTML = `<div class="page-error">${escapeHtml(error.message || "Unable to load candidates.")}</div>`;
  }
}

function section(title, rows) {
  return `<section class="detail-section"><h3>${escapeHtml(title)}</h3><dl class="detail-list">${rows.map(([k,v]) => detailRow(k, v)).join("")}</dl></section>`;
}

async function getJson(url) {
  const response = await fetch(url, { headers: { "Accept": "application/json" }, credentials: "same-origin" });
  const body = await response.json().catch(() => null);
  if (!response.ok) throw new Error(body?.message || body?.error || `Request failed: ${response.status}`);
  return body;
}

async function postJson(url, payload) {
  const response = await fetch(url, { method: "POST", headers: { "Accept": "application/json", "Content-Type": "application/json" }, credentials: "same-origin", body: JSON.stringify(payload) });
  const body = await response.json().catch(() => null);
  if (!response.ok) throw new Error(body?.message || body?.error || `Request failed: ${response.status}`);
  return body;
}

function summaryRow(label, value) { return `<div><dt>${escapeHtml(label)}</dt><dd>${escapeHtml(value ?? "-")}</dd></div>`; }
function detailRow(label, value) { return `<div><dt>${escapeHtml(label)}</dt><dd>${escapeHtml(value ?? "-")}</dd></div>`; }
function startUtcClock() { const c = document.querySelector("#utcClock"); function t(){ c.textContent = new Date().toISOString().replace("T"," ").slice(0,19)+" UTC"; } t(); setInterval(t,1000); }
function money(value) { return Number(value || 0).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 }); }
function showError(message) { const e = document.querySelector("#pageError"); e.hidden = false; e.textContent = message; }
function hideError() { const e = document.querySelector("#pageError"); e.hidden = true; e.textContent = ""; }
function escapeHtml(value) { return String(value ?? "").replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;").replaceAll('"',"&quot;").replaceAll("'","&#039;"); }


function costProfile(staff) {
  const currency = staff.currency_code || "EUR";

  if (staff.staff_role === "TECHNICIAN") {
    return `${money(staff.daily_retainer || 0)} ${currency}/day + ${money(staff.hourly_rate || 0)} ${currency}/h maint.`;
  }

  return `${money(staff.salary_per_flight || 0)} ${currency}/leg + ${money(staff.hourly_rate || 0)} ${currency}/h + ${staff.revenue_share_percent || 0}% rev.`;
}


function staffCostProfile(staff) {
  const currency = staff.currency_code || "EUR";

  if (staff.staff_role === "TECHNICIAN") {
    return `est. ${money(staff.daily_retainer || 0)} ${currency}/day + ${money(staff.hourly_rate || 0)} ${currency}/h maintenance`;
  }

  return `est. ${money(staff.salary_per_flight || 0)} ${currency}/leg + ${money(staff.hourly_rate || 0)} ${currency}/h + ${staff.revenue_share_percent || 0}% revenue`;
}

function candidateCostProfile(candidate) {
  const currency = candidate.currency_code || "EUR";

  if (candidate.staff_role === "TECHNICIAN") {
    return `est. ${money(candidate.daily_retainer || 0)} ${currency}/day + ${money(candidate.hourly_rate || 0)} ${currency}/h maintenance`;
  }

  return `est. ${money(candidate.salary_per_flight || 0)} ${currency}/leg + ${money(candidate.hourly_rate || 0)} ${currency}/h + ${candidate.revenue_share_percent || 0}% revenue`;
}

