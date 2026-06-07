#!/usr/bin/env python3
from pathlib import Path
import re

path = Path("src/js/map-aircraft-left-panel.js")

if not path.exists():
    raise SystemExit("src/js/map-aircraft-left-panel.js not found")

text = path.read_text(encoding="utf-8")

# 1) Ensure crew names print "-" when NULL/empty.
text = text.replace(
    '${row("Pilot 1", crew.pilot_1_name || "-")}',
    '${row("Pilot 1", cleanText(crew.pilot_1_name))}'
)
text = text.replace(
    '${row("Pilot 2", crew.pilot_2_name || "-")}',
    '${row("Pilot 2", cleanText(crew.pilot_2_name))}'
)

# 2) Remove the Company button from the Live aircraft panel.
text = re.sub(
    r'\n\s*<button type="button" id="restoreCompanyPanelButton" class="secondary">Company</button>',
    '',
    text
)

# 3) Remove now-unused button binding in renderAircraftLivePanel.
text = text.replace(
    '\n\n    companyPanelElement.querySelector("#restoreCompanyPanelButton")?.addEventListener("click", restoreCompanyPanel);\n    startPanelTimer(flight);',
    '\n\n    startPanelTimer(flight);'
)

# 4) Add cleanText helper if missing.
if "function cleanText(" not in text:
    marker = "  function row(label, value) {"
    helper = '''
  function cleanText(value) {
    const text = String(value ?? "").trim();

    if (!text || text.toLowerCase() === "null" || text.toLowerCase() === "undefined") {
      return "-";
    }

    return escapeHtml(text);
  }

'''
    if marker not in text:
        raise SystemExit("Could not find row() helper in src/js/map-aircraft-left-panel.js")
    text = text.replace(marker, helper + marker, 1)

path.write_text(text, encoding="utf-8")
print("OK: Live aircraft panel now prints '-' for missing pilots and hides Company button.")
