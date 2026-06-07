#!/usr/bin/env python3
from pathlib import Path

root = Path.cwd()
js_path = root / "src/js/map-aircraft-left-panel.js"
if not js_path.exists():
    raise SystemExit(f"Missing file: {js_path}")

text = js_path.read_text(encoding="utf-8")
original = text


def replace_function(source: str, name: str, replacement: str) -> str:
    marker = f"  function {name}("
    start = source.find(marker)
    if start < 0:
        return source

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

    return source[:start] + replacement.rstrip() + "\n\n" + source[end:]

# Ensure the profit row is present, but compact.
if '${flightProfitRow(flight)}' not in text:
    insertion_points = [
        '          ${row("Passengers", `${flight.passenger_count} / ${flight.passenger_capacity}`)}\n</dl>',
        '          ${row("Passengers", `${flight.passenger_count} / ${flight.passenger_capacity}`)}\n        </dl>',
    ]
    for old in insertion_points:
        if old in text:
            new = old.replace('\n', '\n          ${flightProfitRow(flight)}\n', 1)
            text = text.replace(old, new, 1)
            break
    else:
        raise SystemExit("Could not find the Passengers row insertion point in src/js/map-aircraft-left-panel.js")

# Ensure the click binding is installed after each render.
if 'bindProfitDialog(flight);' not in text:
    old = '    startPanelTimer(flight);'
    if old not in text:
        raise SystemExit("Could not find startPanelTimer(flight) insertion point")
    text = text.replace(old, '    bindProfitDialog(flight);\n    startPanelTimer(flight);', 1)

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

# Replace previous helper implementations if present.
for name, replacement in [
    ("flightProfitRow", flight_profit_row),
    ("bindProfitDialog", bind_profit_dialog),
    ("showFlightProfitDialog", show_profit_dialog),
    ("injectProfitDialogCss", inject_css),
    ("profitClass", profit_class),
    ("money", money),
]:
    text = replace_function(text, name, replacement)

# Insert missing helper functions before row().
helper_marker = '  function row(label, value) {\n    return `<div><dt>${escapeHtml(label)}</dt><dd>${value}</dd></div>`;\n  }'
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
    if helper_marker not in text:
        raise SystemExit("Could not find helper insertion point before row()")
    text = text.replace(helper_marker, "\n\n".join(missing_helpers) + "\n\n" + helper_marker, 1)

if text != original:
    js_path.write_text(text, encoding="utf-8")
    print("Patched src/js/map-aircraft-left-panel.js")
else:
    print("No changes needed: compact live aircraft profit dialog already present")
