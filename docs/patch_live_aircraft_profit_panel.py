#!/usr/bin/env python3
from pathlib import Path

root = Path.cwd()
js_path = root / "src/js/map-aircraft-left-panel.js"
if not js_path.exists():
    raise SystemExit(f"Missing file: {js_path}")

text = js_path.read_text(encoding="utf-8")
original = text

old_row = '          ${row("Passengers", `${flight.passenger_count} / ${flight.passenger_capacity}`)}\n</dl>'
new_row = '          ${row("Passengers", `${flight.passenger_count} / ${flight.passenger_capacity}`)}\n          ${flightProfitRow(flight)}\n</dl>'
if old_row in text:
    text = text.replace(old_row, new_row, 1)
elif '${flightProfitRow(flight)}' not in text:
    raise SystemExit("Could not find the Passengers row insertion point in src/js/map-aircraft-left-panel.js")

helper_marker = '  function row(label, value) {\n    return `<div><dt>${escapeHtml(label)}</dt><dd>${value}</dd></div>`;\n  }'
helpers = '''  function flightProfitRow(flight) {
    const currency = escapeHtml(flight.currency_code || "EUR");
    const profit = Number(flight.profit_amount || 0);
    const revenue = Number(flight.passenger_revenue || 0);
    const cost = Number(flight.total_operating_cost || 0);
    const cssClass = profitClass(profit);
    const label = profit > 0 ? "Profit" : profit < 0 ? "Loss" : "Break-even";

    return row(
      "Estimated result",
      `<span class="${cssClass}">${label}: ${money(profit)} ${currency}</span><small>Revenue ${money(revenue)} ${currency} · Cost ${money(cost)} ${currency}</small>`
    );
  }

  function profitClass(value) {
    const n = Number(value || 0);

    if (n > 0) {
      return "profit-positive";
    }

    if (n < 0) {
      return "profit-negative";
    }

    return "";
  }

  function money(value) {
    const n = Number(value || 0);

    return n.toLocaleString(undefined, {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    });
  }

''' + helper_marker

if 'function flightProfitRow(flight)' not in text:
    if helper_marker not in text:
        raise SystemExit("Could not find helper insertion point in src/js/map-aircraft-left-panel.js")
    text = text.replace(helper_marker, helpers, 1)

if text != original:
    js_path.write_text(text, encoding="utf-8")
    print("Patched src/js/map-aircraft-left-panel.js")
else:
    print("No changes needed: live aircraft profit row already present")
