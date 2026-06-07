#!/usr/bin/env python3
from pathlib import Path

root = Path.cwd()
js_path = root / "src/js/map-aircraft-left-panel.js"
if not js_path.exists():
    raise SystemExit(f"Missing file: {js_path}")

text = js_path.read_text(encoding="utf-8")
original = text


def find_function(source: str, name: str):
    markers = [f"  function {name}(", f"function {name}("]
    start = -1
    for marker in markers:
        start = source.find(marker)
        if start >= 0:
            break
    if start < 0:
        return None

    brace_start = source.find("{", start)
    if brace_start < 0:
        raise SystemExit(f"Could not parse function {name}: missing opening brace")

    depth = 0
    in_string = None
    escaped = False
    in_line_comment = False
    in_block_comment = False
    end = None
    i = brace_start
    while i < len(source):
        ch = source[i]
        nxt = source[i + 1] if i + 1 < len(source) else ""

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
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == in_string:
                in_string = None
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

        if ch in ('"', "'", "`"):
            in_string = ch
            i += 1
            continue

        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                end = i + 1
                break
        i += 1

    if end is None:
        raise SystemExit(f"Could not parse function {name}: missing closing brace")

    while end < len(source) and source[end] in " \t\r\n":
        end += 1

    return start, end


def replace_function(source: str, name: str, replacement: str) -> str:
    found = find_function(source, name)
    if not found:
        return source
    start, end = found
    return source[:start] + replacement.rstrip() + "\n\n" + source[end:]


def insert_before_any_helper(source: str, block: str) -> str:
    # Prefer inserting before a small helper near the end, but fall back safely before the IIFE closure.
    candidates = [
        "  function row(",
        "  function parseUtc(",
        "  function formatDuration(",
        "  function escapeHtml(",
        "})();",
    ]
    for marker in candidates:
        idx = source.find(marker)
        if idx >= 0:
            return source[:idx] + block.rstrip() + "\n\n" + source[idx:]
    raise SystemExit("Could not find any safe helper insertion point")


flight_profit_row = '''  function flightProfitRow(flight) {
    const currency = escapeHtml(flight.currency_code || "EUR");
    const profit = Number(flight.profit_amount || 0);
    const cssClass = profitClass(profit);
    const label = profit > 0 ? "Profit" : profit < 0 ? "Loss" : "Break-even";

    return row(
      "Profit",
      `<button type="button" id="leftPanelProfitButton" class="aircraft-live-profit-button ${cssClass}" title="Show flight economic details">${label}: ${money(profit)} ${currency}</button>`
    );
  }'''

bind_profit_dialog = '''  function bindProfitDialog(flight) {
    const button = companyPanelElement?.querySelector("#leftPanelProfitButton");

    if (!button) {
      return;
    }

    button.addEventListener("click", () => showFlightProfitDialog(flight));
  }'''

show_profit_dialog = '''  function showFlightProfitDialog(flight) {
    const currency = escapeHtml(flight.currency_code || "EUR");
    const profit = Number(flight.profit_amount || 0);
    const revenue = Number(flight.passenger_revenue || 0);
    const cost = Number(flight.total_operating_cost || 0);
    const cssClass = profitClass(profit);
    const label = profit > 0 ? "Profit" : profit < 0 ? "Loss" : "Break-even";

    injectProfitDialogCss();

    const dialog = document.createElement("dialog");
    dialog.className = "aircraft-live-profit-dialog";
    dialog.innerHTML = `
      <form method="dialog" class="aircraft-live-profit-dialog-card">
        <header>
          <div>
            <p class="eyebrow">Flight economics</p>
            <h2>${escapeHtml(flight.flight_code || "Flight")}</h2>
          </div>
          <button type="submit" aria-label="Close">×</button>
        </header>

        <dl>
          ${row("Route", `${escapeHtml(flight.origin_airport_icao_code || "-")} → ${escapeHtml(flight.destination_airport_icao_code || "-")}`)}
          ${row("Passengers", `${escapeHtml(flight.passenger_count ?? "-")} / ${escapeHtml(flight.passenger_capacity ?? "-")}`)}
          ${row("Revenue", `${money(revenue)} ${currency}`)}
          ${row("Operating cost", `${money(cost)} ${currency}`)}
          ${row(label, `<strong class="${cssClass}">${money(profit)} ${currency}</strong>`)}
        </dl>
      </form>
    `;

    document.body.appendChild(dialog);
    dialog.addEventListener("close", () => dialog.remove(), { once: true });

    if (typeof dialog.showModal === "function") {
      dialog.showModal();
      return;
    }

    window.alert(`${label}: ${money(profit)} ${currency}\nRevenue: ${money(revenue)} ${currency}\nCost: ${money(cost)} ${currency}`);
    dialog.remove();
  }'''

inject_css = '''  function injectProfitDialogCss() {
    if (document.querySelector("#icaroLiveAircraftProfitDialogCss")) {
      return;
    }

    const style = document.createElement("style");
    style.id = "icaroLiveAircraftProfitDialogCss";
    style.textContent = `
      .aircraft-live-profit-button {
        border: 0;
        padding: 0;
        background: transparent;
        font: inherit;
        font-weight: 700;
        cursor: pointer;
        text-decoration: underline;
        text-underline-offset: 0.15em;
      }

      .aircraft-live-profit-dialog::backdrop {
        background: rgba(0, 0, 0, 0.45);
      }

      .aircraft-live-profit-dialog {
        border: 0;
        border-radius: 16px;
        padding: 0;
        max-width: min(520px, 92vw);
      }

      .aircraft-live-profit-dialog-card {
        padding: 1.25rem;
        min-width: min(420px, 86vw);
      }

      .aircraft-live-profit-dialog-card header {
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        gap: 1rem;
        margin-bottom: 1rem;
      }

      .aircraft-live-profit-dialog-card header button {
        border: 0;
        background: transparent;
        font-size: 1.5rem;
        cursor: pointer;
      }

      .aircraft-live-profit-dialog-card dl {
        display: grid;
        gap: 0.6rem;
        margin: 0;
      }

      .aircraft-live-profit-dialog-card dl > div {
        display: grid;
        grid-template-columns: 1fr auto;
        gap: 1rem;
        align-items: baseline;
      }

      .aircraft-live-profit-dialog-card dt,
      .aircraft-live-profit-dialog-card dd {
        margin: 0;
      }
    `;
    document.head.appendChild(style);
  }'''

profit_class = '''  function profitClass(value) {
    const n = Number(value || 0);

    if (n > 0) {
      return "profit-positive";
    }

    if (n < 0) {
      return "profit-negative";
    }

    return "";
  }'''

money = '''  function money(value) {
    const n = Number(value || 0);

    return n.toLocaleString(undefined, {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    });
  }'''

# 1) Ensure the row exists in the panel, inserting it just before the closing dl if needed.
if "${flightProfitRow(flight)}" not in text:
    passengers = '${row("Passengers", `${flight.passenger_count} / ${flight.passenger_capacity}`)}'
    idx = text.find(passengers)
    if idx >= 0:
        line_end = text.find("\n", idx)
        if line_end >= 0:
            text = text[:line_end + 1] + "          ${flightProfitRow(flight)}\n" + text[line_end + 1:]
        else:
            text = text[:idx + len(passengers)] + "\n          ${flightProfitRow(flight)}" + text[idx + len(passengers):]
    else:
        dl_idx = text.find("</dl>", text.find("function renderAircraftLivePanel"))
        if dl_idx < 0:
            raise SystemExit("Could not find a safe place to insert the profit row")
        text = text[:dl_idx] + "          ${flightProfitRow(flight)}\n" + text[dl_idx:]

# 2) Ensure the click binding is installed after rendering.
if "bindProfitDialog(flight);" not in text:
    start_call = "    startPanelTimer(flight);"
    idx = text.find(start_call, text.find("function renderAircraftLivePanel"))
    if idx < 0:
        raise SystemExit("Could not find startPanelTimer(flight) in renderAircraftLivePanel")
    text = text[:idx] + "    bindProfitDialog(flight);\n" + text[idx:]

# 3) Replace older helper implementations if they exist.
for name, replacement in [
    ("flightProfitRow", flight_profit_row),
    ("bindProfitDialog", bind_profit_dialog),
    ("showFlightProfitDialog", show_profit_dialog),
    ("injectProfitDialogCss", inject_css),
    ("profitClass", profit_class),
    ("money", money),
]:
    text = replace_function(text, name, replacement)

# 4) Insert missing helpers as one block before an existing helper, no rigid row() dependency.
missing_helpers = []
for fn_name, fn_code in [
    ("flightProfitRow", flight_profit_row),
    ("bindProfitDialog", bind_profit_dialog),
    ("showFlightProfitDialog", show_profit_dialog),
    ("injectProfitDialogCss", inject_css),
    ("profitClass", profit_class),
    ("money", money),
]:
    if f"function {fn_name}(" not in text:
        missing_helpers.append(fn_code)

if missing_helpers:
    text = insert_before_any_helper(text, "\n\n".join(missing_helpers))

if text != original:
    js_path.write_text(text, encoding="utf-8")
    print("Patched src/js/map-aircraft-left-panel.js")
else:
    print("No changes needed: compact live aircraft profit dialog already present")
