#!/usr/bin/env python3
from pathlib import Path
import re

targets = [
    Path("fleet.html"),
    Path("src/js/fleet.js"),
    Path("src/js/fleet-market-table-dialog.js"),
]

def remove_empty_info_boxes(text: str) -> str:
    previous = None

    while previous != text:
        previous = text

        # Remove truly empty info boxes:
        # <div class="info-box"></div>
        # <section class="info-box"> whitespace </section>
        text = re.sub(
            r'\s*<(div|section|aside)\b([^>]*class=["\'][^"\']*\binfo-box\b[^"\']*["\'][^>]*)>\s*</\1>\s*',
            '\n',
            text,
            flags=re.I | re.S
        )

        # Remove template-literal empty info boxes containing only whitespace/newlines.
        text = re.sub(
            r'\s*`?\s*<(div|section|aside)\b([^>]*class=["\'][^"\']*\binfo-box\b[^"\']*["\'][^>]*)>\s*</\1>\s*`?\s*',
            '\n',
            text,
            flags=re.I | re.S
        )

        # Remove info boxes that only contain empty paragraphs/headings/divs.
        text = re.sub(
            r'\s*<(div|section|aside)\b([^>]*class=["\'][^"\']*\binfo-box\b[^"\']*["\'][^>]*)>\s*(?:<(?:p|h2|h3|h4|div|span)[^>]*>\s*</(?:p|h2|h3|h4|div|span)>\s*)+</\1>\s*',
            '\n',
            text,
            flags=re.I | re.S
        )

    return text

changed_any = False

for path in targets:
    if not path.exists():
        print(f"SKIP: {path} not found")
        continue

    original = path.read_text(encoding="utf-8")
    cleaned = remove_empty_info_boxes(original)

    if cleaned != original:
        path.write_text(cleaned, encoding="utf-8")
        changed_any = True
        print(f"OK: removed empty info-box blocks from {path}")
    else:
        print(f"OK: no empty info-box blocks found in {path}")

if not changed_any:
    print("NOTE: no files changed. If the boxes are injected dynamically with another class, send the HTML snippet from browser inspector.")
