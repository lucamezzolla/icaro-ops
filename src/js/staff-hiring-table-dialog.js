(() => {
  const API = {
    candidates: "api/public/staff/candidates.php",
    detail: id => `api/public/staff/candidate-detail.php?id=${encodeURIComponent(id)}`,
    hire: "api/public/staff/hire.php"
  };

  let lastSearch = {
    role: "PILOT",
    q: "",
    fleetOnly: true
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

  function openStaffHiringDialog() {
    const dialog = ensureDialog();
    dialog.showModal();
    renderEmptyState();
  }

  async function loadCandidates() {
    const body = document.querySelector("#staffHiringTableBody");
    const detail = document.querySelector("#staffHiringDetail");
    body.innerHTML = `<p class="muted">Loading candidates...</p>`;
    detail.innerHTML = "";

    lastSearch = readFilters();

    try {
      const params = new URLSearchParams({
        role: lastSearch.role,
        q: lastSearch.q,
        fleetOnly: lastSearch.fleetOnly ? "1" : "0"
      });
      const data = await getJson(`${API.candidates}?${params.toString()}`);
      renderCandidates(body, data.candidates || [], data.fleet_rating_codes || []);
    } catch (error) {
      body.innerHTML = `<div class="page-error">${escapeHtml(error.message || "Unable to load candidates.")}</div>`;
    }
  }

  function readFilters() {
    return {
      role: document.querySelector("#staffCandidateRoleFilter")?.value || "PILOT",
      q: (document.querySelector("#staffCandidateSearch")?.value || "").trim(),
      fleetOnly: Boolean(document.querySelector("#staffCandidateFleetOnly")?.checked)
    };
  }

  function renderEmptyState() {
    const body = document.querySelector("#staffHiringTableBody");
    const detail = document.querySelector("#staffHiringDetail");
    if (!body || !detail) {
      return;
    }
    body.innerHTML = `
      <div class="staff-empty-market">
        <strong>Search candidates to start.</strong>
        <p class="muted">
          The table starts empty. For pilots, keep “Only ratings for my fleet” enabled to find candidates qualified for the aircraft you own.
          Each operational aircraft requires two active qualified pilots.
        </p>
      </div>
    `;
    detail.innerHTML = "";
  }

  function renderCandidates(container, candidates, fleetRatingCodes) {
    if (!candidates.length) {
      container.innerHTML = `
        <div class="staff-empty-market">
          <strong>No matching candidates.</strong>
          <p class="muted">Try another name, license, region or disable the fleet-rating filter.</p>
        </div>
      `;
      return;
    }

    const fleetHint = fleetRatingCodes.length
      ? `<p class="muted">Fleet ratings searched: ${escapeHtml(fleetRatingCodes.join(", "))}. Two active qualified pilots are required for every operational aircraft.</p>`
      : "";

    container.innerHTML = `
      ${fleetHint}
      <table class="compact-dialog-table staff-hiring-table">
        <thead>
          <tr>
            <th>Name</th>
            <th>Role</th>
            <th>Fleet rating match</th>
            <th>Licenses</th>
            <th>Reliability</th>
            <th>Cost</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          ${candidates.map(candidate => `
            <tr>
              <td>
                <strong>${escapeHtml(candidate.display_name)}</strong>
                <div class="muted">${escapeHtml(candidate.home_region_code || "-")} · ${escapeHtml(candidate.experience_level || "-")}</div>
              </td>
              <td>${escapeHtml(candidate.staff_role)}</td>
              <td>${escapeHtml(candidate.fleet_matching_licenses || "-")}</td>
              <td>${escapeHtml(candidate.licenses || "-")}</td>
              <td>${escapeHtml(candidate.reliability_score ?? "-")}</td>
              <td>${escapeHtml(candidateCostProfile(candidate))}</td>
              <td class="row-actions">
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
      await loadCandidates();
      if (typeof window.loadStaff === "function") {
        await window.loadStaff();
      } else {
        document.querySelector("#refreshButton")?.click();
      }
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
          <div class="staff-candidate-filters">
            <label>
              Role
              <select id="staffCandidateRoleFilter">
                <option value="PILOT" selected>Pilots</option>
                <option value="TECHNICIAN">Technicians</option>
                <option value="ALL">All roles</option>
              </select>
            </label>
            <label>
              Search
              <input id="staffCandidateSearch" type="text" placeholder="Name, license, region, experience">
            </label>
            <label class="checkbox-line">
              <input id="staffCandidateFleetOnly" type="checkbox" checked>
              Only ratings for my fleet
            </label>
            <div class="staff-candidate-filter-actions">
              <button id="staffCandidateSearchButton" type="button" class="primary">Search</button>
              <button id="staffCandidateClearButton" type="button">Clear</button>
            </div>
          </div>
          <div id="staffHiringTableBody"></div>
          <div id="staffHiringDetail" class="dialog-detail-panel"></div>
        </div>
        <footer class="dialog-footer">
          <button value="close">Close</button>
        </footer>
      </form>
    `;

    dialog.querySelector(".close-button").addEventListener("click", () => dialog.close());
    dialog.querySelector("#staffCandidateSearchButton").addEventListener("click", loadCandidates);
    dialog.querySelector("#staffCandidateSearch").addEventListener("keydown", event => {
      if (event.key === "Enter") {
        event.preventDefault();
        loadCandidates();
      }
    });
    dialog.querySelector("#staffCandidateClearButton").addEventListener("click", () => {
      dialog.querySelector("#staffCandidateRoleFilter").value = "PILOT";
      dialog.querySelector("#staffCandidateSearch").value = "";
      dialog.querySelector("#staffCandidateFleetOnly").checked = true;
      renderEmptyState();
    });
    dialog.querySelector("#staffCandidateRoleFilter").addEventListener("change", event => {
      const fleetOnly = dialog.querySelector("#staffCandidateFleetOnly");
      if (event.target.value !== "PILOT") {
        fleetOnly.checked = false;
      }
      renderEmptyState();
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

  function candidateCostProfile(candidate) {
    const currency = candidate.currency_code || "EUR";

    if (candidate.staff_role === "TECHNICIAN") {
      return `est. ${money(candidate.daily_retainer || 0)} ${currency}/day + ${money(candidate.hourly_rate || 0)} ${currency}/h maintenance`;
    }

    return `est. ${money(candidate.salary_per_flight || 0)} ${currency}/leg + ${money(candidate.daily_retainer || 0)} ${currency}/day + ${candidate.revenue_share_percent || 0}% revenue`;
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
