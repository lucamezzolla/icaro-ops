#!/usr/bin/env python3
from pathlib import Path
import re

signup_html = Path("signup.html")
if signup_html.exists():
    text = signup_html.read_text(encoding="utf-8")
    patterns = [
        r'<label[^>]*>\s*Company logo.*?</label>',
        r'<div[^>]*class="[^"]*logo[^"]*"[^>]*>.*?</div>',
        r'<input[^>]*(company_logo|logo)[^>]*>\s*',
    ]
    for pattern in patterns:
        text = re.sub(pattern, '', text, flags=re.I | re.S)
    signup_html.write_text(text, encoding="utf-8")
    print("OK: signup.html logo field removed if present.")

signup_js = Path("src/js/signup.js")
if signup_js.exists():
    text = signup_js.read_text(encoding="utf-8")
    text = re.sub(r'\s*company_logo[^,\n]*,?\n', '\n', text, flags=re.I)
    text = re.sub(r'\s*logo_url[^,\n]*,?\n', '\n', text, flags=re.I)
    signup_js.write_text(text, encoding="utf-8")
    print("OK: signup.js logo payload removed if present.")

signup_php = Path("api/public/signup.php")
if signup_php.exists():
    text = signup_php.read_text(encoding="utf-8")
    text = re.sub(
        r'([\'"]?budget_amount[\'"]?\s*=>\s*)[0-9]+(?:\.[0-9]+)?',
        r'\g<1>8500000.00',
        text
    )
    text = re.sub(r'(initialBudget\s*=\s*)[0-9]+(?:\.[0-9]+)?', r'\g<1>8500000.00', text)
    text = re.sub(r'(budgetAmount\s*=\s*)[0-9]+(?:\.[0-9]+)?', r'\g<1>8500000.00', text)
    for old in ['3500000.00', '3790000.00', '4000000.00', '4500000.00', '5000000.00', '6000000.00']:
        text = text.replace(old, '8500000.00')
    signup_php.write_text(text, encoding="utf-8")
    print("OK: signup.php initial budget set to 8,500,000 when matching patterns exist.")
