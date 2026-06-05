#!/usr/bin/env python3
from pathlib import Path

path = Path("src/js/staff.js")
text = path.read_text(encoding="utf-8")

text = text.replace(
    "Candidate hiring remains connected to the existing staff APIs. If candidates are available, they appear here.",
    "Candidate costs are indicative estimates. Operational policy: 2 qualified pilots per aircraft, and 1 qualified technician recommended every 3 aircraft."
)

old_open = '''async function openAddStaffDialog() {
  const dialog = document.querySelector("#addStaffDialog");
  const list = document.querySelector("#candidateList");
  list.textContent = "Loading candidates...";
  dialog.showModal();'''

new_open = '''async function openAddStaffDialog() {
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
  dialog.showModal();'''

if old_open in text:
    text = text.replace(old_open, new_open)

old_candidate = '''<p class="muted">${escapeHtml(c.staff_role || "-")} · Reliability ${escapeHtml(c.reliability_score ?? "-")} · Salary ${money(c.salary_per_flight || 0)} ${escapeHtml(c.currency_code || "EUR")}</p>'''
new_candidate = '''<p class="muted">
            ${escapeHtml(c.staff_role || "-")} · Reliability ${escapeHtml(c.reliability_score ?? "-")} ·
            Indicative cost: ${candidateCostProfile(c)}
          </p>
          <p class="muted">Licenses: ${escapeHtml(c.licenses || "-")}</p>'''
text = text.replace(old_candidate, new_candidate)

text = text.replace("<th>Cost/flight</th>", "<th>Indicative cost</th>")
text = text.replace("<th>Cost profile</th>", "<th>Indicative cost</th>")
text = text.replace("${costProfile(s)}", "${staffCostProfile(s)}")
text = text.replace('${money(s.salary_per_flight || 0)} ${escapeHtml(s.currency_code || "EUR")}', '${staffCostProfile(s)}')

text = text.replace('["Salary per flight", `${money(staff.salary_per_flight)} ${staff.currency_code || "EUR"}`]', '["Indicative leg fee", `${money(staff.salary_per_flight)} ${staff.currency_code || "EUR"}`]')
text = text.replace('["Revenue share", `${staff.revenue_share_percent || 0}%`]', '["Revenue share estimate", `${staff.revenue_share_percent || 0}%`]')

helper = r'''
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
'''

if "function staffCostProfile(" not in text:
    text += "\n" + helper + "\n"

path.write_text(text, encoding="utf-8")
print("OK: staff UI patched.")
