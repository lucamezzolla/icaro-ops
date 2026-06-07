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

new_top_toolbar = '''<div class="fleet-page-actions" aria-label="Fleet actions">
          <button id="buyAircraftButton" type="button" class="icon-button" title="Buy aircraft" aria-label="Buy aircraft">+</button>
          <button id="refreshButton" type="button" class="icon-button" title="Refresh fleet" aria-label="Refresh fleet">↻</button>
        </div>'''

# Remove existing fleet table toolbar, including the previous + and refresh placement inside the card/table area.
html = re.sub(
    r"\n?[ \t]*<div\b[^>]*class=[\"'][^\"']*fleet-table-actions[^\"']*[\"'][^>]*>.*?</div>",
    "",
    html,
    flags=re.IGNORECASE | re.DOTALL,
)

# Remove any remaining standalone buttons with the two ids. They will be reinserted in the page header.
html = re.sub(
    r"\n?[ \t]*<button\b[^>]*\bid=[\"'](?:buyAircraftButton|refreshButton)[\"'][^>]*>.*?</button>",
    "",
    html,
    flags=re.IGNORECASE | re.DOTALL,
)

# If the previous patch added a fleet-table-card-header class, remove only that modifier.
def clean_class_attr(match: re.Match) -> str:
    quote = match.group(1)
    classes = match.group(2).split()
    classes = [c for c in classes if c != "fleet-table-card-header"]
    return f'class={quote}{" ".join(classes)}{quote}'
html = re.sub(r"class=([\"'])([^\"']*)\1", clean_class_attr, html)

# Remove an empty card header left by earlier toolbar placement, if it exists directly before the table wrap.
html = re.sub(
    r"\n[ \t]*<div\b[^>]*class=[\"'][^\"']*card-header[^\"']*[\"'][^>]*>\s*</div>\s*(?=\n[ \t]*<div\b[^>]*class=[\"']table-wrap[\"'])",
    "",
    html,
    flags=re.IGNORECASE | re.DOTALL,
)

# Insert the new toolbar inside the page header, after the textual header block.
page_header_pattern = re.compile(
    r"(<section\b[^>]*class=[\"'][^\"']*page-header[^\"']*[\"'][^>]*>)(.*?)(</section>)",
    flags=re.IGNORECASE | re.DOTALL,
)

m = page_header_pattern.search(html)
if not m:
    raise SystemExit("Could not find page-header section in fleet.html")

section_open, section_body, section_close = m.group(1), m.group(2), m.group(3)

# Remove stale page actions if rerun.
section_body = re.sub(
    r"\n?[ \t]*<div\b[^>]*class=[\"'][^\"']*fleet-page-actions[^\"']*[\"'][^>]*>.*?</div>",
    "",
    section_body,
    flags=re.IGNORECASE | re.DOTALL,
)

# Remove old textual top button variants in page header, if present.
section_body = re.sub(
    r"\n?[ \t]*<button\b(?![^>]*\bid=)[^>]*>\s*(?:New airplane|Buy aircraft|Refresh)\s*</button>",
    "",
    section_body,
    flags=re.IGNORECASE | re.DOTALL,
)

section_body = section_body.rstrip() + "\n        " + new_top_toolbar + "\n      "

html = html[:m.start()] + section_open + section_body + section_close + html[m.end():]

# Safety checks: exactly one of each id, both inside the page-header.
if len(re.findall(r"id=[\"']buyAircraftButton[\"']", html)) != 1:
    raise SystemExit("Patch safety check failed: expected exactly one buyAircraftButton")
if len(re.findall(r"id=[\"']refreshButton[\"']", html)) != 1:
    raise SystemExit("Patch safety check failed: expected exactly one refreshButton")

page_header_after = page_header_pattern.search(html).group(0)
if "buyAircraftButton" not in page_header_after or "refreshButton" not in page_header_after:
    raise SystemExit("Patch safety check failed: toolbar was not inserted inside page-header")
if "fleet-table-actions" in html:
    raise SystemExit("Patch safety check failed: old fleet-table-actions still present")

fleet_html.write_text(html, encoding="utf-8")

css = fleet_css.read_text(encoding="utf-8")
css_block = r'''

/* Fleet page toolbar: compact actions in the top-right page header. */
.fleet-page-actions {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 8px;
  margin-left: auto;
}

.fleet-page-actions .icon-button {
  min-width: 42px;
  height: 38px;
  padding: 0 12px;
  display: inline-grid;
  place-items: center;
  font-size: 1.15rem;
  line-height: 1;
}
'''

if "Fleet page toolbar: compact actions" not in css:
    css = css.rstrip() + css_block + "\n"

# Neutralize the old table-toolbar alignment block if present: harmless if no elements use it,
# but avoid forcing card headers to the right in future.
css = css.replace("/* Fleet table toolbar: compact actions above the owned aircraft table. */", "/* Fleet table toolbar: legacy styles kept unused. */")

fleet_css.write_text(css, encoding="utf-8")

print("Patched fleet.html and src/css/fleet.css")
