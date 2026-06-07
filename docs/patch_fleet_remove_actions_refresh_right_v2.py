#!/usr/bin/env python3
from pathlib import Path
import re

ROOT = Path.cwd()
FLEET_HTML = ROOT / "fleet.html"
FLEET_JS = ROOT / "src/js/fleet.js"
FLEET_CSS = ROOT / "src/css/fleet.css"


def remove_function(source: str, name: str) -> str:
    markers = [f"function {name}", f"async function {name}"]
    start = -1
    for marker in markers:
        start = source.find(marker)
        if start >= 0:
            break
    if start < 0:
        return source

    brace = source.find("{", start)
    if brace < 0:
        return source

    depth = 0
    i = brace
    in_string = None
    escaped = False

    while i < len(source):
        ch = source[i]
        if in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == in_string:
                in_string = None
        else:
            if ch in ('"', "'", "`"):
                in_string = ch
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    end = i + 1
                    while end < len(source) and source[end] in " \t\r\n":
                        end += 1
                    return source[:start].rstrip() + "\n\n" + source[end:]
        i += 1

    return source


def patch_html():
    text = FLEET_HTML.read_text(encoding="utf-8")
    original = text

    # Give the small Refresh toolbar a dedicated class, preserving the current simplified header.
    text = re.sub(
        r'<div class="card-header(?: fleet-card-header| fleet-table-header)?">\s*\n\s*<button id="refreshButton" type="button">Refresh</button>\s*\n\s*</div>',
        '<div class="card-header fleet-table-header">\n            <button id="refreshButton" type="button">Refresh</button>\n          </div>',
        text,
        count=1,
        flags=re.S,
    )

    if text == original and 'id="refreshButton"' in text and 'fleet-table-header' not in text:
        raise SystemExit("Could not find the Fleet Refresh header. Please send: grep -n \"refreshButton\" -C 3 fleet.html")

    FLEET_HTML.write_text(text, encoding="utf-8")


def patch_js():
    text = FLEET_JS.read_text(encoding="utf-8")
    original = text

    # Remove the old body Actions block inserted by a previous patch.
    # Match the specific class first: <section class="detail-section aircraft-detail-actions"> ... </section>
    text = re.sub(
        r'\n\s*<section\s+class="[^"]*\baircraft-detail-actions\b[^"]*">[\s\S]*?\n\s*</section>',
        '',
        text,
        flags=re.I,
    )

    # Fallback: remove an Actions section only when it contains the old detail-image marker.
    text = re.sub(
        r'\n\s*<section\s+class="[^"]*\bdetail-section\b[^"]*">\s*\n\s*<h3>Actions</h3>[\s\S]*?data-aircraft-detail-image[\s\S]*?\n\s*</section>',
        '',
        text,
        flags=re.I,
    )

    # Remove the old binding call used only by that body Actions section.
    text = text.replace('\n    bindAircraftDetailActions(content, a);', '')
    text = text.replace('\n  bindAircraftDetailActions(content, a);', '')

    # Remove the helper if it survived and is no longer needed.
    text = remove_function(text, "bindAircraftDetailActions")

    if "aircraft-detail-actions" in text:
        raise SystemExit("The aircraft-detail-actions block is still present. Please send: grep -n \"aircraft-detail-actions\\|<h3>Actions\" -C 5 src/js/fleet.js")

    # Do not reject generic words named Actions elsewhere; only the aircraft-detail body section was targeted.
    FLEET_JS.write_text(text, encoding="utf-8")

    if text != original:
        print("Patched src/js/fleet.js")


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
    print("Patched Fleet: removed body Actions section and right-aligned Refresh.")


if __name__ == "__main__":
    main()
