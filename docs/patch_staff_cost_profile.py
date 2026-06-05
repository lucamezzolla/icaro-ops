#!/usr/bin/env python3
from pathlib import Path

path = Path("src/js/staff.js")
text = path.read_text(encoding="utf-8")

text = text.replace(
    '<th>Cost/flight</th>',
    '<th>Cost profile</th>'
)

text = text.replace(
    '${money(s.salary_per_flight || 0)} ${escapeHtml(s.currency_code || "EUR")}',
    '${costProfile(s)}'
)

if "function costProfile(" not in text:
    text += r'''

function costProfile(staff) {
  const currency = staff.currency_code || "EUR";

  if (staff.staff_role === "TECHNICIAN") {
    return `${money(staff.daily_retainer || 0)} ${currency}/day + ${money(staff.hourly_rate || 0)} ${currency}/h maint.`;
  }

  return `${money(staff.salary_per_flight || 0)} ${currency}/leg + ${money(staff.hourly_rate || 0)} ${currency}/h + ${staff.revenue_share_percent || 0}% rev.`;
}
'''

path.write_text(text, encoding="utf-8")
print("OK: staff.js cost profile updated.")
