from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
fleet_html = ROOT / "fleet.html"
fleet_js = ROOT / "src/js/fleet.js"
remove_rule_js = ROOT / "src/js/aircraft-market-remove-buy-rule-column.js"

if not fleet_html.exists():
    raise SystemExit("fleet.html not found")
if not fleet_js.exists():
    raise SystemExit("src/js/fleet.js not found")

# 1) Remove the redundant Owned aircraft title/description, keeping only the Refresh button.
html = fleet_html.read_text(encoding="utf-8")
html_original = html

html = re.sub(
    r'''\n\s*<div>\s*\n\s*<h2>Owned aircraft</h2>\s*\n\s*<p>Essential data only\. Open details for technical and financial information\.</p>\s*\n\s*</div>''',
    "",
    html,
    count=1,
    flags=re.MULTILINE,
)

# Keep the new clearer column name, if a previous patch did not already apply it.
html = html.replace("<th>Airport</th>", "<th>Last position</th>")
html = html.replace("<th>Airports</th>", "<th>Last position</th>")

if html != html_original:
    fleet_html.write_text(html, encoding="utf-8")
    print("Patched fleet.html")
else:
    print("fleet.html already patched")

# 2) Physically remove the Buy Rule/Budget only column from the Buy aircraft catalog renderer,
#    so we do not need a broad DOM cleanup to keep the UI clean.
js = fleet_js.read_text(encoding="utf-8")
js_original = js

js = re.sub(
    r'''\n\s*<th>\s*BUY RULE\s*</th>''',
    "",
    js,
    flags=re.IGNORECASE,
)

# Remove the exact catalog status cell that printed Need budget / Budget only.
js = re.sub(
    r'''\n\s*<td>\s*\n\s*<span class="badge \$\{a\.can_afford === false \? "warn" : "good"\}">\s*\n\s*\$\{a\.can_afford === false \? "Need budget" : "Budget only"\}\s*\n\s*</span>\s*\n\s*</td>''',
    "",
    js,
    flags=re.MULTILINE,
)

# If an older patch left an empty header before the actions column, keep only one action header.
js = js.replace("\n<th></th>\n<th></th>", "\n<th></th>")

# Ensure owned Fleet table says In flight in Last position for flying aircraft.
js = re.sub(
    r'if \(status === "IN_FLIGHT"\) \{\s*return "[^"]*";\s*\}',
    'if (status === "IN_FLIGHT") {\n    return "In flight";\n  }',
    js,
    count=1,
    flags=re.MULTILINE,
)

if js != js_original:
    fleet_js.write_text(js, encoding="utf-8")
    print("Patched src/js/fleet.js")
else:
    print("src/js/fleet.js already patched")

# 3) Replace the previous broad cleanup script with a safe scoped version.
#    The old version scanned every table and could remove Fleet columns on Refresh.
if remove_rule_js.exists():
    remove_rule_js.write_text(r'''(() => {
  document.addEventListener("DOMContentLoaded", () => {
    removeBuyRuleColumnsFromAircraftMarketOnly();
    installBuyRuleColumnObserver();
  });

  function installBuyRuleColumnObserver() {
    const catalogContainer = document.querySelector("#aircraftCatalogList");

    if (!catalogContainer) {
      return;
    }

    const observer = new MutationObserver(() => {
      removeBuyRuleColumnsFromAircraftMarketOnly();
    });

    observer.observe(catalogContainer, {
      childList: true,
      subtree: true
    });
  }

  function removeBuyRuleColumnsFromAircraftMarketOnly() {
    const dialog = document.querySelector("#buyAircraftDialog");

    if (!dialog) {
      return;
    }

    dialog.querySelectorAll("table").forEach(table => {
      const index = findBuyRuleColumnIndex(table);

      if (index < 0) {
        return;
      }

      table.querySelectorAll("tr").forEach(row => {
        const cells = Array.from(row.children);

        if (cells[index]) {
          cells[index].remove();
        }
      });
    });
  }

  function findBuyRuleColumnIndex(table) {
    const headers = Array.from(table.querySelectorAll("thead th"));
    const headerIndex = headers.findIndex(header => normalize(header.textContent) === "BUY RULE");

    if (headerIndex >= 0) {
      return headerIndex;
    }

    const bodyRows = Array.from(table.querySelectorAll("tbody tr"));

    if (!bodyRows.length) {
      return -1;
    }

    const maxCells = Math.max(0, ...bodyRows.map(row => row.children.length));

    for (let index = 0; index < maxCells; index += 1) {
      const values = bodyRows
        .map(row => normalize(row.children[index]?.textContent || ""))
        .filter(Boolean);

      if (!values.length) {
        continue;
      }

      const buyRuleValues = values.filter(value =>
        value === "BUDGET ONLY" ||
        value === "NEED BUDGET"
      );

      if (buyRuleValues.length === values.length) {
        return index;
      }
    }

    return -1;
  }

  function normalize(value) {
    return String(value || "")
      .replace(/\s+/g, " ")
      .trim()
      .toUpperCase();
  }
})();
''', encoding="utf-8")
    print("Patched src/js/aircraft-market-remove-buy-rule-column.js")
else:
    print("src/js/aircraft-market-remove-buy-rule-column.js not found; skipped")
