(() => {
  const API = {
    candidates: "api/public/staff/candidates.php",
    detail: id => `api/public/staff/candidate-detail.php?id=${encodeURIComponent(id)}`,
    hire: "api/public/staff/hire.php"
  };

  document.addEventListener("click", event => {
    const target = event.target.closest("button, a");

    if (!target || target.closest("#staffHiringTableDialog")) {
      return;
    }

    const label = (target.textContent || "").trim().toLowerCase();

    if (label.includes("add staff") || label.includes("hire staff")) {
      event.preventDefault();
      event.stopPropagation();
      event.stopImmediatePropagation();
      openStaffHiringDialog();
    }
  }, true);

  async function openStaffHiringDialog() {
    const dialog = ensureDialog();
    dialog.showModal();
    await loadCandidates("ALL");
  }

  async function loadCandidates(role) {
    const body = document.querySelector("#staffHiringTableBody");
    body.innerHTML = `<p class="muted">Loading candidates...</p>`;

    try {
      const data = await getJson(`${API.candidates}?role=${encodeURIComponent(role)}`);
      renderCandidates(body, data.candidates || []);
    } catch (error) {
      body.innerHTML = `<div class="page-error">${escapeHtml(error.message || "Unable to load candidates.")}</div>`;
    }
  }

  function renderCandidates(container, candidates) {
    if (!candidates.length) {
      container.innerHTML = `<p class="muted">No candidates available.</p>`;
      return;
    }

    container.innerHTML = `
      <table class="compact-dialog-table">
        <thead>
          <tr>
            <th>Name</th>
            <th>Role</th>
            <th>Region</th>
            <th>Experience</th>
            <th>Licenses</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          ${candidates.map(candidate => `
            <tr>
              <td><strong>${escapeHtml(candidate.display_name)}</strong></td>
              <td>${escapeHtml(candidate.staff_role)}</td>
              <td>${escapeHtml(candidate.home_region_code || "-")}</td>
              <td>${escapeHtml(candidate.experience_level || "-")}</td>
              <td>${escapeHtml(candidate.licenses || "-")}</td>
              <td>
                <button type="button" data-candidate-detail="${candidate.id}">Details</button>
                <button type="button" data-candidate-hire="${candidate.id}" class="primary">Hire</button>
              </td>
            </tr>
          `).join("")}
        </tbody>
      </table>
    `;

    container.querySelectorAll("[data-candidate-detail]").forEach(button => {
      button.addEventListener("click", () => showCandidateDetail(Number(button.dataset.candidateDetail)));
    });

    container.querySelectorAll("[data-candidate-hire]").forEach(button => {
      button.addEventListener("click", () => hireCandidate(Number(button.dataset.candidateHire)));
    });
  }

  async function showCandidateDetail(id) {
    const detail = document.querySelector("#staffHiringDetail");
    detail.innerHTML = `<p class="muted">Loading detail...</p>`;

    try {
      const data = await getJson(API.detail(id));
      const c = data.candidate;
      const licenses = data.licenses || [];

      detail.innerHTML = `
        <section class="detail-section">
          <h3>${escapeHtml(c.display_name)}</h3>
          <dl class="detail-list">
            ${detailRow("Role", c.staff_role)}
            ${detailRow("Region", c.home_region_code)}
            ${detailRow("Age", c.age_years)}
            ${detailRow("Experience", c.experience_level)}
            ${detailRow("Reliability", c.reliability_score)}
            ${detailRow("Discipline", c.discipline_score)}
            ${detailRow("Teamwork", c.teamwork_score)}
            ${detailRow("Stress tolerance", c.stress_tolerance_score)}
            ${detailRow("Flight hours", c.flight_hours_total)}
            ${detailRow("Maintenance hours", c.aircraft_maintenance_hours_total)}
            ${detailRow("Salary per flight", `${money(c.salary_per_flight)} ${c.currency_code}`)}
            ${detailRow("Daily retainer", `${money(c.daily_retainer)} ${c.currency_code}`)}
            ${detailRow("Hiring bonus", `${money(c.hiring_bonus)} ${c.currency_code}`)}
            ${detailRow("Licenses", licenses.map(l => `${l.license_code} (${l.proficiency_score})`).join(", ") || "-")}
          </dl>
        </section>
      `;
    } catch (error) {
      detail.innerHTML = `<div class="page-error">${escapeHtml(error.message || "Unable to load candidate detail.")}</div>`;
    }
  }

  async function hireCandidate(id) {
    if (!confirm("Hire this candidate?")) {
      return;
    }

    try {
      const result = await postJson(API.hire, { candidate_id: id });
      alert(`Hired: ${result.display_name}`);
      await loadCandidates(document.querySelector("#staffCandidateRoleFilter")?.value || "ALL");
    } catch (error) {
      alert(error.message || "Unable to hire candidate.");
    }
  }

  function ensureDialog() {
    let dialog = document.querySelector("#staffHiringTableDialog");

    if (dialog) {
      return dialog;
    }

    dialog = document.createElement("dialog");
    dialog.id = "staffHiringTableDialog";
    dialog.innerHTML = `
      <form method="dialog" class="dialog-card wide-dialog">
        <header class="dialog-header">
          <div>
            <p class="eyebrow">Hiring</p>
            <h2>Add staff</h2>
          </div>
          <button type="button" class="close-button" aria-label="Close">×</button>
        </header>
        <div class="dialog-body">
          <label>
            Candidate type
            <select id="staffCandidateRoleFilter">
              <option value="ALL">All roles</option>
              <option value="PILOT">Pilots</option>
              <option value="TECHNICIAN">Technicians</option>
            </select>
          </label>
          <p class="muted">
            Candidate names are worldwide. Pilot candidates include type ratings generated from all aircraft models in the database.
          </p>
          <div id="staffHiringTableBody"></div>
          <div id="staffHiringDetail" class="dialog-detail-panel"></div>
        </div>
        <footer class="dialog-footer">
          <button value="close">Close</button>
        </footer>
      </form>
    `;

    dialog.querySelector(".close-button").addEventListener("click", () => dialog.close());
    dialog.querySelector("#staffCandidateRoleFilter").addEventListener("change", event => {
      loadCandidates(event.target.value);
    });

    document.body.appendChild(dialog);

    return dialog;
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
      headers: { "Accept": "application/json", "Content-Type": "application/json" },
      credentials: "same-origin",
      body: JSON.stringify(payload)
    });
    const body = await response.json().catch(() => null);
    if (!response.ok) {
      throw new Error(body?.message || body?.error || `Request failed: ${response.status}`);
    }
    return body;
  }

  function detailRow(label, value) {
    return `<div><dt>${escapeHtml(label)}</dt><dd>${escapeHtml(value ?? "-")}</dd></div>`;
  }

  function money(value) {
    return Number(value || 0).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  }

  function escapeHtml(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }
})();
