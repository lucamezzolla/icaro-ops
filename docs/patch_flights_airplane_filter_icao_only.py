#!/usr/bin/env python3
from pathlib import Path

PROJECT = Path.cwd()
ROUTES_JS = PROJECT / "src/js/routes.js"

def read(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path}")
    return path.read_text(encoding="utf-8")

def write(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")

def replace_function(js: str, name: str, new_body: str) -> str:
    marker = "function " + name + "("
    start = js.find(marker)
    if start < 0:
        return js

    brace = js.find("{", start)
    if brace < 0:
        return js

    depth = 0
    i = brace
    in_string = None
    escape = False
    in_line_comment = False
    in_block_comment = False
    template_depth = 0

    while i < len(js):
        ch = js[i]
        nxt = js[i + 1] if i + 1 < len(js) else ""

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
                return js[:start] + new_body.rstrip() + js[i + 1:]

        i += 1

    return js

NEW_MATCHES = '''function flightMatchesAirplaneFilter(flight, filterValue) {
  const icaoCodes = flightAirplaneIcaoCodes(flight);

  /*
   * Airplane filter is intentionally ICAO-only.
   *
   * Examples:
   * - A or A3 or A320 => matches A320
   * - C or CONC => matches CONC
   * - manufacturer/model names are ignored
   */
  return icaoCodes.some(code => code.startsWith(filterValue));
}'''

NEW_TOKENS = '''function flightAirplaneSearchTokens(flight) {
  return flightAirplaneIcaoCodes(flight);
}'''

NEW_TEXT = '''function flightAirplaneSearchText(flight) {
  return flightAirplaneIcaoCodes(flight).join(" ");
}

function flightAirplaneIcaoCodes(flight) {
  return [
    flight.compatible_aircraft_icao_codes,
    flight.icao_type_code
  ]
    .flatMap(splitSearchTokens)
    .filter(Boolean);
}'''

def main() -> None:
    js = read(ROUTES_JS)

    old_condition = '''    if (airplane && !flightAirplaneSearchText(flight).includes(airplane)) {
      return false;
    }'''
    new_condition = '''    if (airplane && !flightMatchesAirplaneFilter(flight, airplane)) {
      return false;
    }'''
    if old_condition in js:
        js = js.replace(old_condition, new_condition, 1)

    if "function flightMatchesAirplaneFilter(" in js:
        js = replace_function(js, "flightMatchesAirplaneFilter", NEW_MATCHES)
    else:
        marker = "\nfunction flightAirplaneSearchText(flight) {"
        if marker not in js:
            raise RuntimeError("Could not find airplane filter functions in src/js/routes.js")
        js = js.replace(marker, "\n" + NEW_MATCHES + "\n" + marker, 1)

    if "function flightAirplaneSearchTokens(" in js:
        js = replace_function(js, "flightAirplaneSearchTokens", NEW_TOKENS)

    if "function flightAirplaneSearchText(" in js:
        js = replace_function(js, "flightAirplaneSearchText", NEW_TEXT)
    else:
        js += "\n\n" + NEW_TEXT + "\n"

    if "function splitSearchTokens(" not in js:
        js += '''
function splitSearchTokens(value) {
  return String(value || "")
    .toUpperCase()
    .split(/[^A-Z0-9]+/)
    .map(token => token.trim())
    .filter(Boolean);
}
'''

    write(ROUTES_JS, js)
    print("Patched Flights airplane filter: ICAO code only.")

if __name__ == "__main__":
    main()
