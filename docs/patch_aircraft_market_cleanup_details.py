#!/usr/bin/env python3
from pathlib import Path
import re

targets = [
    Path("src/js/fleet-market-table-dialog.js"),
    Path("src/js/fleet.js"),
]

def add_helpers(text: str) -> str:
    helper = '''
function resolveAircraftModelId(row) {
  const candidates = [
    row.aircraft_model_id,
    row.aircraftModelId,
    row.model_id,
    row.modelId,
    row.id
  ];

  for (const value of candidates) {
    const number = Number(value);

    if (Number.isInteger(number) && number > 0) {
      return number;
    }
  }

  return null;
}

function removeBuyRuleColumnFromAircraftTables(root = document) {
  root.querySelectorAll("table").forEach(table => {
    const headers = Array.from(table.querySelectorAll("thead th, tr:first-child th"));
    const index = headers.findIndex(header => header.textContent.trim().toUpperCase() === "BUY RULE");

    if (index < 0) {
      return;
    }

    table.querySelectorAll("tr").forEach(row => {
      const cells = Array.from(row.children);

      if (cells[index]) {
        cells[index].remove();
      }
    });
  });
}

'''
    if "function resolveAircraftModelId(" not in text:
        marker = "function escapeHtml"
        if marker in text:
            text = text.replace(marker, helper + marker, 1)
        else:
            text += "\n" + helper
    return text

def remove_buy_rule_literals(text: str) -> str:
    text = re.sub(
        r'\s*<th[^>]*>\s*BUY RULE\s*</th>\s*',
        '\n',
        text,
        flags=re.I
    )

    text = re.sub(
        r'\s*<td[^>]*>\s*\$\{[^}]*buy[^}]*rule[^}]*\}\s*</td>\s*',
        '\n',
        text,
        flags=re.I
    )
    text = re.sub(
        r'\s*<td[^>]*>\s*\$\{[^}]*purchase[^}]*rule[^}]*\}\s*</td>\s*',
        '\n',
        text,
        flags=re.I
    )
    text = re.sub(
        r'\s*<td[^>]*>\s*(?:Budget only|Budget|Open market|Available)\s*</td>\s*',
        '\n',
        text,
        flags=re.I
    )

    text = re.sub(
        r'["\']BUY RULE["\']\s*,?',
        '',
        text,
        flags=re.I
    )

    return text

def patch_detail_buttons(text: str) -> str:
    text = text.replace(
        'data-aircraft-detail="${row.aircraft_model_id || row.id}"',
        'data-aircraft-detail="${resolveAircraftModelId(row) || ""}"'
    )
    text = text.replace(
        'data-aircraft-detail="${a.aircraft_model_id || a.id}"',
        'data-aircraft-detail="${resolveAircraftModelId(a) || ""}"'
    )
    text = text.replace(
        'data-model-detail="${a.aircraft_model_id || a.id}"',
        'data-model-detail="${resolveAircraftModelId(a) || ""}"'
    )
    text = text.replace(
        'data-model-detail="${row.aircraft_model_id || row.id}"',
        'data-model-detail="${resolveAircraftModelId(row) || ""}"'
    )

    text = text.replace(
        'showAircraftDetail(Number(button.dataset.aircraftDetail))',
        'showAircraftDetailFromButton(button)'
    )
    text = text.replace(
        'openAircraftDetail(Number(button.dataset.aircraftDetail))',
        'openAircraftDetailFromButton(button)'
    )
    text = text.replace(
        'showAircraftDetail(Number(button.dataset.modelDetail))',
        'showAircraftDetailFromButton(button)'
    )
    text = text.replace(
        'openAircraftDetail(Number(button.dataset.modelDetail))',
        'openAircraftDetailFromButton(button)'
    )

    safe_handlers = '''
function aircraftModelIdFromButton(button) {
  const raw = button.dataset.aircraftDetail || button.dataset.modelDetail || "";
  const id = Number(raw);

  return Number.isInteger(id) && id > 0 ? id : null;
}

function showAircraftDetailFromButton(button) {
  const id = aircraftModelIdFromButton(button);

  if (!id) {
    alert("Aircraft details are not available for this row because the model id is missing.");
    return;
  }

  showAircraftDetail(id);
}

function openAircraftDetailFromButton(button) {
  const id = aircraftModelIdFromButton(button);

  if (!id) {
    alert("Aircraft details are not available for this row because the model id is missing.");
    return;
  }

  openAircraftDetail(id);
}

'''
    if "function aircraftModelIdFromButton(" not in text:
        marker = "function escapeHtml"
        if marker in text:
            text = text.replace(marker, safe_handlers + marker, 1)
        else:
            text += "\n" + safe_handlers

    return text

def add_runtime_cleanup(text: str) -> str:
    markers = [
        "renderAircraftTable(body, sortAircraftByPurchasePrice(aircraft));",
        "renderAircraftTable(body, aircraft);",
        "renderAircraftCatalog(sortAircraftByPurchasePrice(catalogAircraft));",
        "renderAircraftCatalog(catalogAircraft);",
    ]

    for marker in markers:
        if marker in text and "removeBuyRuleColumnFromAircraftTables(document);" not in text:
            text = text.replace(
                marker,
                marker + "\n      removeBuyRuleColumnFromAircraftTables(document);",
                1
            )

    return text

for path in targets:
    if not path.exists():
        print(f"SKIP: {path} not found")
        continue

    text = path.read_text(encoding="utf-8")
    original = text

    text = add_helpers(text)
    text = remove_buy_rule_literals(text)
    text = patch_detail_buttons(text)
    text = add_runtime_cleanup(text)

    if text != original:
        path.write_text(text, encoding="utf-8")
        print(f"OK: patched {path}")
    else:
        print(f"OK: no changes needed for {path}")
