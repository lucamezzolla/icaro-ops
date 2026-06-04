# Auth guard for protected pages

This patch adds a browser-side guard for protected pages.

## Files

```text
src/js/auth-guard.js
src/js/login.js
login.html
```

## Apply

```bash
cd /home/luca/Documenti/html/icaro-ops
unzip -o /home/luca/Scaricati/icaro-ops-auth-guard-patch.zip
```

## Add the guard to protected pages

Add this script before the page-specific script.

### index.html

Before:

```html
<script src="src/js/dashboard-map.js"></script>
```

add:

```html
<script src="src/js/auth-guard.js"></script>
```

### fleet.html

Before:

```html
<script src="src/js/fleet.js"></script>
```

add:

```html
<script src="src/js/auth-guard.js"></script>
```

Quick command:

```bash
python3 - <<'PY'
from pathlib import Path

changes = {
    "index.html": ('<script src="src/js/dashboard-map.js"></script>',
                   '<script src="src/js/auth-guard.js"></script>\n  <script src="src/js/dashboard-map.js"></script>'),
    "fleet.html": ('<script src="src/js/fleet.js"></script>',
                   '<script src="src/js/auth-guard.js"></script>\n  <script src="src/js/fleet.js"></script>'),
}

for filename, (old, new) in changes.items():
    path = Path(filename)
    text = path.read_text(encoding="utf-8")
    if 'src/js/auth-guard.js' not in text:
        text = text.replace(old, new)
        path.write_text(text, encoding="utf-8")
        print(f"OK: added auth guard to {filename}")
    else:
        print(f"SKIP: auth guard already present in {filename}")
PY
```

## Behavior

Opening:

```text
http://127.0.0.1:8080/index.html
```

without a valid PHP session redirects to:

```text
login.html?next=index.html
```

After login, the user returns to the requested page.

`login.html` includes a visible link to:

```text
signup.html
```

## Notes

This is a frontend guard for user experience. The real security must remain server-side too: every API that reads or modifies company data should eventually verify the authenticated PHP session and not trust client-supplied company IDs.
