#!/usr/bin/env python3
from pathlib import Path
import re

ROOT = Path.cwd()
FLEET_HTML = ROOT / "fleet.html"
FLEET_JS = ROOT / "src/js/fleet.js"
FLEET_CSS = ROOT / "src/css/fleet.css"


def patch_html():
    text = FLEET_HTML.read_text(encoding="utf-8")

    # Add a dedicated class only to the Owned Fleet card header that contains Refresh.
    patterns = [
        (
            r'<div class="card-header">\s*\n\s*<button id="refreshButton" type="button">Refresh</button>\s*\n\s*</div>',
            '<div class="card-header fleet-table-header">\n            <button id="refreshButton" type="button">Refresh</button>\n          </div>',
        ),
        (
            r'<div class="card-header fleet-card-header">\s*\n\s*<button id="refreshButton" type="button">Refresh</button>\s*\n\s*</div>',
            '<div class="card-header fleet-table-header">\n            <button id="refreshButton" type="button">Refresh</button>\n          </div>',
        ),
    ]

    changed = False
    for pattern, replacement in patterns:
        text, count = re.subn(pattern, replacement, text, count=1, flags=re.S)
        if count:
            changed = True
            break

    if not changed and 'id="refreshButton"' in text and 'fleet-table-header' not in text:
        raise SystemExit("Could not add fleet-table-header class around Refresh button")

    FLEET_HTML.write_text(text, encoding="utf-8")


def remove_actions_section_from_template(text: str) -> str:
    before = text

    # Remove a literal detail-section block whose title is Actions.
    text = re.sub(
        r'''\n\s*<section\s+class=["']detail-section["']>\s*\n\s*<h3>Actions</h3>.*?\n\s*</section>''',
        "",
        text,
        flags=re.S | re.I,
    )

    # Remove an expression-based section("Actions", [...]) if a previous patch used the helper.
    text = re.sub(
        r'''\n\s*\$\{\s*section\(\s*["']Actions["']\s*,\s*\[[\s\S]*?\]\s*\)\s*\}''',
        "",
        text,
        flags=re.S,
    )

    # Remove old inline action rows if they survived inside another section.
    text = re.sub(
        r'''\n\s*\$\{\s*detailRow\(\s*["']Actions["'][\s\S]*?\)\s*\}''',
        "",
        text,
        flags=re.S,
    )

    return text


def patch_js():
    text = FLEET_JS.read_text(encoding="utf-8")
    patched = remove_actions_section_from_template(text)

    if patched == text and re.search(r'<h3>Actions</h3>|section\(\s*["\']Actions["\']', text):
        raise SystemExit("Found an Actions section, but could not remove it safely")

    FLEET_JS.write_text(patched, encoding="utf-8")


def patch_css():
    css = FLEET_CSS.read_text(encoding="utf-8")
    append = r'''

/* Fleet owned-aircraft toolbar. */
.fleet-table-header {
  justify-content: flex-end;
  align-items: center;
}

.fleet-table-header #refreshButton {
  margin-left: auto;
}
'''
    if "/* Fleet owned-aircraft toolbar. */" not in css:
        css += append
    FLEET_CSS.write_text(css, encoding="utf-8")


def main():
    if not FLEET_HTML.exists() or not FLEET_JS.exists() or not FLEET_CSS.exists():
        raise SystemExit("Run this script from the icaro-ops project root")

    patch_html()
    patch_js()
    patch_css()
    print("Patched Fleet detail Actions section removal and right-aligned Refresh button.")


if __name__ == "__main__":
    main()
