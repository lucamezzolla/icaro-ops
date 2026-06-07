#!/usr/bin/env python3
from pathlib import Path

ROOT = Path.cwd()
css_path = ROOT / "src/css/staff.css"
append_path = ROOT / "docs/staff_candidate_filter_css_append.css"
marker = "/* Staff hiring search dialog. */"

if not css_path.exists():
    raise SystemExit("Missing src/css/staff.css")
if not append_path.exists():
    raise SystemExit("Missing docs/staff_candidate_filter_css_append.css")

css = css_path.read_text(encoding="utf-8")
if marker not in css:
    css_path.write_text(css.rstrip() + "\n" + append_path.read_text(encoding="utf-8"), encoding="utf-8")
    print("Updated src/css/staff.css")
else:
    print("src/css/staff.css already contains the staff hiring filter styles")
