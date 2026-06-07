#!/usr/bin/env python3
from pathlib import Path
import re

JS_TARGETS = [
    Path("src/js/fleet-market-table-dialog.js"),
    Path("src/js/fleet.js"),
]

PHP_TARGET_DIRS = [
    Path("api/public/fleet"),
]

JS_HELPER = """
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

function resolveAircraftModelCode(row) {
  return String(row.model_code || row.modelCode || "").trim();
}

function resolveAircraftIcaoCode(row) {
  return String(row.icao_type_code || row.icaoTypeCode || row.icao || "").trim();
}

function removeBuyRuleColumnFromAircraftTables(root = document) {
  root.querySelectorAll("table").forEach(table => {
    let removeIndex = -1;

    const headers = Array.from(table.querySelectorAll("thead th, tr:first-child th"));
    removeIndex = headers.findIndex(header => header.textContent.trim().toUpperCase() === "BUY RULE");

    if (removeIndex < 0) {
      const rows = Array.from(table.querySelectorAll("tbody tr, tr")).filter(row => row.querySelector("td"));
      const maxCells = Math.max(0, ...rows.map(row => row.children.length));

      for (let index = 0; index < maxCells; index += 1) {
        const values = rows
          .map(row => row.children[index]?.textContent.trim().toUpperCase() || "")
          .filter(Boolean);

        if (
          values.length > 0 &&
          values.every(value => value === "BUDGET ONLY" || value === "OPEN MARKET" || value === "AVAILABLE")
        ) {
          removeIndex = index;
          break;
        }
      }
    }

    if (removeIndex < 0) {
      return;
    }

    table.querySelectorAll("tr").forEach(row => {
      const cells = Array.from(row.children);

      if (cells[removeIndex]) {
        cells[removeIndex].remove();
      }
    });
  });
}

"""

SAFE_HANDLERS = """
function aircraftModelIdFromButton(button) {
  const raw = button.dataset.aircraftDetail || button.dataset.modelDetail || "";
  const id = Number(raw);

  return Number.isInteger(id) && id > 0 ? id : null;
}

async function showAircraftDetailFromButton(button) {
  const id = aircraftModelIdFromButton(button);

  if (id) {
    showAircraftDetail(id);
    return;
  }

  const modelCode = button.dataset.aircraftModelCode || "";
  const icao = button.dataset.aircraftIcao || "";

  if (typeof showAircraftDetailByCode === "function" && (modelCode || icao)) {
    await showAircraftDetailByCode(modelCode, icao);
    return;
  }

  alert("Aircraft details are not available for this row because the model id is missing.");
}

async function openAircraftDetailFromButton(button) {
  const id = aircraftModelIdFromButton(button);

  if (id) {
    openAircraftDetail(id);
    return;
  }

  const modelCode = button.dataset.aircraftModelCode || "";
  const icao = button.dataset.aircraftIcao || "";

  if (typeof openAircraftDetailByCode === "function" && (modelCode || icao)) {
    await openAircraftDetailByCode(modelCode, icao);
    return;
  }

  alert("Aircraft details are not available for this row because the model id is missing.");
}

"""

PHP_FALLBACK = """
function resolve_aircraft_model_id_from_request(PDO $pdo): int
{
    $id = isset($_GET['id']) ? (int)$_GET['id'] : 0;

    if ($id > 0) {
        return $id;
    }

    $modelCode = trim((string)($_GET['model_code'] ?? $_GET['modelCode'] ?? ''));
    $icao = trim((string)($_GET['icao'] ?? $_GET['icao_type_code'] ?? $_GET['icaoTypeCode'] ?? ''));

    if ($modelCode !== '') {
        $stmt = $pdo->prepare('SELECT id FROM aircraft_models WHERE model_code = :model_code LIMIT 1');
        $stmt->execute(['model_code' => $modelCode]);
        $found = (int)($stmt->fetchColumn() ?: 0);

        if ($found > 0) {
            return $found;
        }
    }

    if ($icao !== '') {
        $stmt = $pdo->prepare('SELECT id FROM aircraft_models WHERE icao_type_code = :icao ORDER BY new_purchase_price ASC, id ASC LIMIT 1');
        $stmt->execute(['icao' => $icao]);
        $found = (int)($stmt->fetchColumn() ?: 0);

        if ($found > 0) {
            return $found;
        }
    }

    return 0;
}

"""

def add_before_escape_html(text: str, helper: str, marker_name: str) -> str:
    if marker_name in text:
        return text

    marker = "function escapeHtml"
    if marker in text:
        return text.replace(marker, helper + marker, 1)

    return text + "\n" + helper

def patch_js(text: str) -> str:
    # Remove source-rendered BUY RULE header/cell if present.
    text = re.sub(
        r'\s*<th[^>]*>\s*(?:BUY\s*RULE|Buy\s*rule)\s*</th>\s*',
        '\n',
        text,
        flags=re.I
    )

    text = re.sub(
        r'\s*<td[^>]*>\s*(?:<[^>]+>)*\s*(?:Budget\s*only|Open\s*market|Available)\s*(?:</[^>]+>)*\s*</td>\s*',
        '\n',
        text,
        flags=re.I | re.S
    )

    text = re.sub(
        r'\s*<td[^>]*>\s*\$\{[^}]*?(?:buy_rule|buyRule|purchase_rule|purchaseRule)[^}]*?\}\s*</td>\s*',
        '\n',
        text,
        flags=re.I | re.S
    )

    # Do not remove the literal BUY RULE from JS comparisons.
    text = add_before_escape_html(text, JS_HELPER, "function resolveAircraftModelId(")

    # Make buttons more robust when possible.
    button_replacements = [
        (
            'data-aircraft-detail="${row.aircraft_model_id || row.id}"',
            'data-aircraft-detail="${resolveAircraftModelId(row) || ""}" data-aircraft-model-code="${escapeHtml(resolveAircraftModelCode(row))}" data-aircraft-icao="${escapeHtml(resolveAircraftIcaoCode(row))}"'
        ),
        (
            'data-aircraft-detail="${a.aircraft_model_id || a.id}"',
            'data-aircraft-detail="${resolveAircraftModelId(a) || ""}" data-aircraft-model-code="${escapeHtml(resolveAircraftModelCode(a))}" data-aircraft-icao="${escapeHtml(resolveAircraftIcaoCode(a))}"'
        ),
        (
            'data-model-detail="${a.aircraft_model_id || a.id}"',
            'data-model-detail="${resolveAircraftModelId(a) || ""}" data-aircraft-model-code="${escapeHtml(resolveAircraftModelCode(a))}" data-aircraft-icao="${escapeHtml(resolveAircraftIcaoCode(a))}"'
        ),
        (
            'data-model-detail="${row.aircraft_model_id || row.id}"',
            'data-model-detail="${resolveAircraftModelId(row) || ""}" data-aircraft-model-code="${escapeHtml(resolveAircraftModelCode(row))}" data-aircraft-icao="${escapeHtml(resolveAircraftIcaoCode(row))}"'
        ),
    ]

    for old, new in button_replacements:
        text = text.replace(old, new)

    text = text.replace('showAircraftDetail(Number(button.dataset.aircraftDetail))', 'showAircraftDetailFromButton(button)')
    text = text.replace('openAircraftDetail(Number(button.dataset.aircraftDetail))', 'openAircraftDetailFromButton(button)')
    text = text.replace('showAircraftDetail(Number(button.dataset.modelDetail))', 'showAircraftDetailFromButton(button)')
    text = text.replace('openAircraftDetail(Number(button.dataset.modelDetail))', 'openAircraftDetailFromButton(button)')

    text = add_before_escape_html(text, SAFE_HANDLERS, "function aircraftModelIdFromButton(")

    render_markers = [
        "renderAircraftTable(body, sortAircraftByPurchasePrice(aircraft));",
        "renderAircraftTable(body, aircraft);",
        "renderAircraftCatalog(sortAircraftByPurchasePrice(catalogAircraft));",
        "renderAircraftCatalog(catalogAircraft);",
        "renderAircraftTable(container, sortAircraftByPurchasePrice(aircraft));",
        "renderAircraftTable(container, aircraft);",
    ]

    for marker in render_markers:
        cleanup = marker + "\n      removeBuyRuleColumnFromAircraftTables(document);"
        if marker in text and cleanup not in text:
            text = text.replace(marker, cleanup, 1)

    return text

def patch_php_list_endpoint(text: str) -> str:
    if "aircraft_models" not in text:
        return text

    if "aircraft_model_id" in text:
        return text

    if "FROM aircraft_models am" in text:
        return re.sub(r"SELECT\s+", "SELECT am.id AS aircraft_model_id, ", text, count=1, flags=re.I)

    if "FROM aircraft_models" in text:
        return re.sub(r"SELECT\s+", "SELECT id AS aircraft_model_id, ", text, count=1, flags=re.I)

    return text

def patch_php_detail_endpoint(text: str) -> str:
    if "INVALID_MODEL_ID" not in text:
        return text

    if "function resolve_aircraft_model_id_from_request(" not in text:
        pos = text.find("<?php")
        if pos >= 0:
            line_end = text.find("\n", pos)
            text = text[:line_end + 1] + PHP_FALLBACK + text[line_end + 1:]

    patterns = [
        r"\$modelId\s*=\s*\(int\)\(\$_GET\['id'\]\s*\?\?\s*0\)\s*;",
        r"\$model_id\s*=\s*\(int\)\(\$_GET\['id'\]\s*\?\?\s*0\)\s*;",
        r"\$aircraftModelId\s*=\s*\(int\)\(\$_GET\['id'\]\s*\?\?\s*0\)\s*;",
    ]

    for pattern in patterns:
        text = re.sub(pattern, "$modelId = resolve_aircraft_model_id_from_request($pdo);", text)

    return text

changed = False

for path in JS_TARGETS:
    if not path.exists():
        print(f"SKIP: {path} not found")
        continue

    original = path.read_text(encoding="utf-8")
    patched = patch_js(original)

    if patched != original:
        path.write_text(patched, encoding="utf-8")
        changed = True
        print(f"OK: patched JS {path}")
    else:
        print(f"OK: no JS changes needed for {path}")

for directory in PHP_TARGET_DIRS:
    if not directory.exists():
        print(f"SKIP: {directory} not found")
        continue

    for path in directory.glob("*.php"):
        original = path.read_text(encoding="utf-8")
        patched = patch_php_list_endpoint(original)
        patched = patch_php_detail_endpoint(patched)

        if patched != original:
            path.write_text(patched, encoding="utf-8")
            changed = True
            print(f"OK: patched PHP {path}")

if not changed:
    print("NOTE: no files changed. Send this output:")
    print('grep -R "Budget only\\|BUY RULE\\|INVALID_MODEL_ID\\|aircraft_model_id" -n src/js api/public/fleet')
