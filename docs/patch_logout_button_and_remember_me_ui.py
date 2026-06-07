#!/usr/bin/env python3
from pathlib import Path
import re

logout_script = '<script src="src/js/auth-session-ui.js"></script>'
remember_script = '<script src="src/js/login-remember-me.js"></script>'

def add_script(html, script):
    if script in html:
        return html
    if "</body>" in html:
        return html.replace("</body>", f"  {script}\n</body>")
    return html + "\n" + script + "\n"

def add_logout_button(html):
    if "data-logout-button" in html or 'id="logoutButton"' in html:
        return html
    button = '<button id="logoutButton" type="button" data-logout-button>Logout</button>'
    for closing in ["</nav>", "</header>"]:
        if closing in html:
            return html.replace(closing, f"          {button}\n        {closing}", 1)
    match = re.search(r"<body[^>]*>", html)
    if match:
        return html[:match.end()] + f"\n  {button}\n" + html[match.end():]
    return button + "\n" + html

def add_remember_checkbox(html):
    if 'id="rememberMe"' in html or 'name="remember_me"' in html:
        return html

    checkbox = (
        "\n          <label class=\"remember-me-row\">\n"
        "            <input id=\"rememberMe\" name=\"remember_me\" type=\"checkbox\">\n"
        "            <span>Remember me on this browser</span>\n"
        "          </label>\n"
    )

    for pattern in [
        r"(<button[^>]*type=[\"']submit[\"'][^>]*>)",
        r"(<button[^>]*>[ \t\n\r]*Login[ \t\n\r]*</button>)",
    ]:
        match = re.search(pattern, html, flags=re.I)
        if match:
            return html[:match.start()] + checkbox + html[match.start():]

    return html.replace("</form>", checkbox + "\n        </form>", 1) if "</form>" in html else html + checkbox

for path in Path(".").glob("*.html"):
    text = path.read_text(encoding="utf-8")
    original = text
    lower_name = path.name.lower()

    if lower_name == "login.html":
        text = add_remember_checkbox(text)
        text = add_script(text, remember_script)
    elif lower_name not in {"register.html", "signup.html"}:
        text = add_logout_button(text)
        text = add_script(text, logout_script)

    if text != original:
        path.write_text(text, encoding="utf-8")
        print(f"OK: patched {path}")
    else:
        print(f"OK: no changes needed for {path}")
