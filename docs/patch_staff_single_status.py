#!/usr/bin/env python3
from pathlib import Path

PROJECT = Path.cwd()
STAFF_JS = PROJECT / "src/js/staff.js"

def read(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path}")
    return path.read_text(encoding="utf-8")

def write(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")

def remove_function(content: str, function_name: str) -> str:
    start = content.find("function " + function_name + "(")
    if start < 0:
        return content

    brace = content.find("{", start)
    if brace < 0:
        return content

    depth = 0
    i = brace
    in_string = None
    escape = False
    in_line_comment = False
    in_block_comment = False
    template_depth = 0

    while i < len(content):
        ch = content[i]
        nxt = content[i + 1] if i + 1 < len(content) else ""

        if in_line_comment:
            if ch == "\n":
                in_line_comment = False
            i += 1
            continue

        if in_block_comment:
            if ch == "*" and nxt == "/":
                in_block_comment = False
                i += 2
                continue
            i += 1
            continue

        if in_string:
            if escape:
                escape = False
                i += 1
                continue
            if ch == "\\":
                escape = True
                i += 1
                continue
            if in_string == "`":
                if ch == "$" and nxt == "{":
                    template_depth += 1
                    i += 2
                    continue
                if ch == "}" and template_depth > 0:
                    template_depth -= 1
                    i += 1
                    continue
                if ch == "`" and template_depth == 0:
                    in_string = None
                    i += 1
                    continue
            elif ch == in_string:
                in_string = None
                i += 1
                continue
            i += 1
            continue

        if ch == "/" and nxt == "/":
            in_line_comment = True
            i += 2
            continue
        if ch == "/" and nxt == "*":
            in_block_comment = True
            i += 2
            continue
        if ch in ("'", '"', "`"):
            in_string = ch
            i += 1
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return content[:start] + content[i + 1:]
        i += 1

    return content

def main() -> None:
    js = read(STAFF_JS)

    old_two_badge_cell = '<td>${staffStatusBadges(s)}</td>'
    new_single_badge_cell = '<td>${staffStatusBadge(s)}</td>'

    if old_two_badge_cell in js:
        js = js.replace(old_two_badge_cell, new_single_badge_cell, 1)
    else:
        old_original_cell = '<td><span class="badge ${s.employment_status === "ACTIVE" ? "good" : "warn"}">${escapeHtml(s.employment_status || "-")}</span></td>'
        if old_original_cell in js:
            js = js.replace(old_original_cell, new_single_badge_cell, 1)
        elif "staffStatusBadge(s)" not in js:
            raise RuntimeError("Could not find the Staff status table cell in src/js/staff.js")

    js = remove_function(js, "staffStatusBadges")

    if "function staffStatusBadge(" not in js:
        helper = '''
function staffStatusBadge(s) {
  const status = staffEffectiveStatus(s);
  const badgeClass = status === "AVAILABLE" ? "good" : "warn";
  return `<span class="badge ${badgeClass}">${escapeHtml(status)}</span>`;
}

function staffEffectiveStatus(s) {
  const operationalStatus = s.operational_status || "AVAILABLE";
  const employmentStatus = s.employment_status || "-";

  if (employmentStatus !== "ACTIVE") {
    return employmentStatus;
  }

  if (operationalStatus && operationalStatus !== "AVAILABLE") {
    return operationalStatus === "IN_FLIGHT" ? "IN FLIGHT / BUSY" : operationalStatus;
  }

  return "AVAILABLE";
}
'''
        marker = "\nfunction staffCostProfile("
        if marker in js:
            js = js.replace(marker, helper + marker, 1)
        else:
            js += "\n" + helper

    old_detail_rows = '["Employment status", staff.employment_status],\n          ["Operational status", staff.operational_status || "AVAILABLE"],'
    new_detail_rows = '["Status", staffEffectiveStatus(staff)],'

    if old_detail_rows in js:
        js = js.replace(old_detail_rows, new_detail_rows, 1)
    else:
        old_detail_status = '["Status", staff.employment_status],'
        if old_detail_status in js:
            js = js.replace(old_detail_status, new_detail_rows, 1)

    write(STAFF_JS, js)
    print("Patched Staff UI: Status is now a single effective status.")

if __name__ == "__main__":
    main()
