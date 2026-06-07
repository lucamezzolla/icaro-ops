#!/usr/bin/env python3
from pathlib import Path

path = Path("src/js/fleet.js")
text = path.read_text(encoding="utf-8")

text = text.replace(
"""    <div class="info-box">
      <strong>Current level aircraft market</strong>
      <p>
        This table only shows aircraft available for your current operating level.
        Endgame aircraft such as Concorde stay locked until later progression.
      </p>
      <p>
        Qualified pilots: ${escapeHtml(pilotCoverage.current_qualified_pilots ?? "-")}.
        Required for current fleet: ${escapeHtml(pilotCoverage.required_pilots_for_current_fleet ?? "-")}.
      </p>
    </div>""",
"""    <div class="info-box">
      <strong>Development open aircraft market</strong>
      <p>
        All aircraft models are visible for testing. Purchase is limited only by company budget.
      </p>
      <p>
        Pilot qualifications, base level, reputation, endgame locks and progression rules are disabled in this development market.
      </p>
    </div>"""
)

text = text.replace("<th>Pilot coverage</th>", "<th>Buy rule</th>")

text = text.replace(
"""              <td>
                <span class="badge ${a.pilot_coverage_ok_after_purchase ? "good" : "warn"}">
                  ${escapeHtml(a.current_qualified_pilots ?? "-")} / ${escapeHtml(a.required_pilots_after_purchase ?? "-")}
                </span>
              </td>""",
"""              <td>
                <span class="badge ${a.can_afford === false ? "warn" : "good"}">
                  ${a.can_afford === false ? "Need budget" : "Budget only"}
                </span>
              </td>"""
)

text = text.replace(
"""    if (code === "INSUFFICIENT_QUALIFIED_PILOTS") {
      lines.push("Pilot coverage is not sufficient for this purchase.");

      if (
        body?.required_pilots_after_purchase !== undefined &&
        body?.current_qualified_pilots !== undefined
      ) {
        const missingPilots = Math.max(
          0,
          Number(body.required_pilots_after_purchase) - Number(body.current_qualified_pilots)
        );

        lines.push(`You need ${missingPilots} more qualified pilots to buy this aircraft.`);
      }

      if (body?.required_license) {
        lines.push(`Required aircraft qualification: ${body.required_license}`);
      }
    } else {
      lines.push(body?.message || code || `Request failed: ${response.status}`);
    }""",
"""    if (code === "INSUFFICIENT_FUNDS") {
      lines.push(body?.message || "Company budget is not enough to buy this aircraft.");

      if (body?.missing_amount !== undefined) {
        lines.push(`Missing amount: ${body.missing_amount}`);
      }
    } else {
      lines.push(body?.message || code || `Request failed: ${response.status}`);
    }"""
)

path.write_text(text, encoding="utf-8")
print("OK: fleet.js now presents the market as budget-only.")
