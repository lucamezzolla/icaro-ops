#!/usr/bin/env python3
from pathlib import Path
import re

def fix_php_strict_types(path: Path) -> bool:
    if not path.exists():
        print(f"SKIP: {path} not found")
        return False

    text = path.read_text(encoding="utf-8")
    original = text

    if "<?php" not in text:
        print(f"SKIP: {path} is not a PHP file")
        return False

    # Remove every existing strict_types declaration, wherever previous patches placed it.
    text = re.sub(r"\s*declare\s*\(\s*strict_types\s*=\s*1\s*\)\s*;\s*", "\n", text)

    # Put declare immediately after <?php, which is required by PHP.
    text = text.replace("<?php", "<?php\ndeclare(strict_types=1);\n", 1)

    # If a resolver function exists, make sure it accepts modelId too.
    text = text.replace(
        "$id = isset($_GET['id']) ? (int)$_GET['id'] : 0;",
        "$id = isset($_GET['modelId']) ? (int)$_GET['modelId'] : (isset($_GET['id']) ? (int)$_GET['id'] : 0);"
    )

    # Patch common strict id extraction patterns to accept modelId as well.
    replacements = {
        "$modelId = (int)($_GET['id'] ?? 0);":
            "$modelId = (int)($_GET['modelId'] ?? $_GET['id'] ?? 0);",
        "$model_id = (int)($_GET['id'] ?? 0);":
            "$model_id = (int)($_GET['modelId'] ?? $_GET['id'] ?? 0);",
        "$aircraftModelId = (int)($_GET['id'] ?? 0);":
            "$aircraftModelId = (int)($_GET['modelId'] ?? $_GET['id'] ?? 0);",
        "$modelId = (int)($_GET['modelId'] ?? 0);":
            "$modelId = (int)($_GET['modelId'] ?? $_GET['id'] ?? 0);",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    # If previous patch inserted resolver before declare, it is now after declare because declare was reinserted at the top.
    if text != original:
        path.write_text(text, encoding="utf-8")
        print(f"OK: fixed strict_types/modelId in {path}")
        return True

    print(f"OK: no strict_types/modelId changes needed in {path}")
    return False

def add_script_to_fleet_html() -> bool:
    path = Path("fleet.html")
    if not path.exists():
        print("SKIP: fleet.html not found")
        return False

    script = '<script src="src/js/aircraft-market-remove-buy-rule-column.js"></script>'
    text = path.read_text(encoding="utf-8")
    original = text

    if script in text:
        print("OK: fleet.html already includes buy-rule column remover")
        return False

    if "</body>" in text:
        text = text.replace("</body>", f"  {script}\n</body>")
    else:
        text += "\n" + script + "\n"

    path.write_text(text, encoding="utf-8")
    print("OK: added buy-rule column remover to fleet.html")
    return True

changed = False

changed = fix_php_strict_types(Path("api/public/fleet/model-detail.php")) or changed
changed = add_script_to_fleet_html() or changed

if not changed:
    print("NOTE: no files changed.")
