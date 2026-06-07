#!/usr/bin/env python3
from pathlib import Path
import re

path = Path("api/public/auth/login.php")
if not path.exists():
    raise SystemExit("api/public/auth/login.php not found")

text = path.read_text(encoding="utf-8")

if "remember-login.php" not in text:
    require_line = "require_once __DIR__ . '/../../lib/remember-login.php';\n"
    last_require = None
    for match in re.finditer(r"require(?:_once)?\s+[^;]+;\s*", text):
        last_require = match
    if last_require:
        text = text[:last_require.end()] + require_line + text[last_require.end():]
    else:
        text = text.replace("<?php", "<?php\n" + require_line, 1)

payload_var = None
payload_match = re.search(r"\$(\w+)\s*=\s*read_json_body\s*\(\s*\)\s*;", text)
if payload_match:
    payload_var = "$" + payload_match.group(1)

call = f"remember_login_if_requested({payload_var if payload_var else 'null'});"

if "remember_login_if_requested(" not in text:
    index = text.rfind("json_response(")
    if index == -1:
        raise SystemExit("Could not find json_response() in login.php; add remember_login_if_requested() manually after successful authentication.")
    text = text[:index] + call + "\n\n" + text[index:]

path.write_text(text, encoding="utf-8")
print("OK: patched api/public/auth/login.php for remember-me session persistence.")
