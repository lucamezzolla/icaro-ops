#!/usr/bin/env python3
from pathlib import Path
import re

root = Path.cwd()
fleet_html = root / "fleet.html"
fleet_css = root / "src/css/fleet.css"

if not fleet_html.exists():
    raise SystemExit("fleet.html not found. Run this script from the project root.")
if not fleet_css.exists():
    raise SystemExit("src/css/fleet.css not found. Run this script from the project root.")

html = fleet_html.read_text(encoding="utf-8")
original_html = html

# Remove any existing buy-aircraft button first. The new one will be placed next to Refresh.
html = re.sub(
    r"\n?[ \t]*<button\b[^>]*\bid=[\"']buyAircraftButton[\"'][^>]*>.*?</button>",
    "",
    html,
    flags=re.IGNORECASE | re.DOTALL,
)

# Remove a top-level New airplane / Buy aircraft button without id, but only inside the page header.
def clean_page_header(match: re.Match) -> str:
    block = match.group(0)
    block = re.sub(
        r"\n?[ \t]*<button\b(?![^>]*\bid=)[^>]*>\s*(?:New airplane|Buy aircraft)\s*</button>",
        "",
        block,
        flags=re.IGNORECASE | re.DOTALL,
    )
    return block

html = re.sub(
    r"<section\b[^>]*class=[\"'][^\"']*page-header[^\"']*[\"'][^>]*>.*?</section>",
    clean_page_header,
    html,
    flags=re.IGNORECASE | re.DOTALL,
)

new_toolbar = '''<div class="fleet-table-actions" aria-label="Fleet table actions">
              <button id="buyAircraftButton" type="button" class="icon-button" title="Buy aircraft" aria-label="Buy aircraft">+</button>
              <button id="refreshButton" type="button" class="icon-button" title="Refresh fleet" aria-label="Refresh fleet">↻</button>
            </div>'''

# If a previous toolbar exists, replace it cleanly.
if "fleet-table-actions" in html:
    html = re.sub(
        r"<div\b[^>]*class=[\"'][^\"']*fleet-table-actions[^\"']*[\"'][^>]*>.*?</div>",
        new_toolbar,
        html,
        flags=re.IGNORECASE | re.DOTALL,
        count=1,
    )
else:
    # Replace the existing refresh button with the new two-button toolbar.
    html, count = re.subn(
        r"<button\b[^>]*\bid=[\"']refreshButton[\"'][^>]*>.*?</button>",
        new_toolbar,
        html,
        flags=re.IGNORECASE | re.DOTALL,
        count=1,
    )
    if count == 0:
        raise SystemExit("Could not find refreshButton in fleet.html")

# Make the card header containing the toolbar right-aligned.
# Add the modifier class to the closest ordinary card-header opening tag if not already present.
if "fleet-table-card-header" not in html:
    toolbar_pos = html.find("fleet-table-actions")
    before = html[:toolbar_pos]
    idx = before.rfind('<div class="card-header"')
    if idx == -1:
        # Alternate quote/order tolerant fallback.
        matches = list(re.finditer(r"<div\b[^>]*class=[\"'][^\"']*card-header[^\"']*[\"'][^>]*>", before, flags=re.IGNORECASE))
        if not matches:
            raise SystemExit("Could not find card-header before fleet-table-actions")
        m = matches[-1]
        tag = m.group(0)
        if "fleet-table-card-header" not in tag:
            new_tag = re.sub(r"class=([\"'])([^\"']*)\1", lambda cm: f'class={cm.group(1)}{cm.group(2)} fleet-table-card-header{cm.group(1)}', tag, count=1)
            html = html[:m.start()] + new_tag + html[m.end():]
    else:
        html = html[:idx] + '<div class="card-header fleet-table-card-header"' + html[idx + len('<div class="card-header"'):]

# Ensure there is exactly one buyAircraftButton and one refreshButton.
if len(re.findall(r"id=[\"']buyAircraftButton[\"']", html)) != 1:
    raise SystemExit("Patch safety check failed: expected exactly one buyAircraftButton")
if len(re.findall(r"id=[\"']refreshButton[\"']", html)) != 1:
    raise SystemExit("Patch safety check failed: expected exactly one refreshButton")

if html != original_html:
    fleet_html.write_text(html, encoding="utf-8")
else:
    print("fleet.html already looked patched")

css = fleet_css.read_text(encoding="utf-8")
css_block = r'''

/* Fleet table toolbar: compact actions above the owned aircraft table. */
.fleet-table-card-header {
  justify-content: flex-end;
  align-items: center;
}

.fleet-table-actions {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 8px;
  margin-left: auto;
}

.fleet-table-actions .icon-button {
  min-width: 42px;
  height: 38px;
  padding: 0 12px;
  display: inline-grid;
  place-items: center;
  font-size: 1.15rem;
  line-height: 1;
}
'''

if "Fleet table toolbar: compact actions" not in css:
    fleet_css.write_text(css.rstrip() + css_block + "\n", encoding="utf-8")

print("Patched fleet.html and src/css/fleet.css")
