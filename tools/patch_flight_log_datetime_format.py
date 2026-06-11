#!/usr/bin/env python3
from pathlib import Path

path = Path('src/js/flight-log.js')
if not path.exists():
    raise SystemExit('ERROR: src/js/flight-log.js not found. Run this script from the project root.')

text = path.read_text(encoding='utf-8')
original = text

replacements = {
    '<td>${escapeHtml(f.actual_departure_at_utc || f.scheduled_departure_at_utc || "-")}</td>':
    '<td>${escapeHtml(formatFlightLogDateTime(f.actual_departure_at_utc || f.scheduled_departure_at_utc))}</td>',
    '<td>${escapeHtml(f.actual_arrival_at_utc || f.scheduled_arrival_at_utc || "-")}</td>':
    '<td>${escapeHtml(formatFlightLogDateTime(f.actual_arrival_at_utc || f.scheduled_arrival_at_utc))}</td>',
}

for old, new in replacements.items():
    if old in text:
        text = text.replace(old, new, 1)
    elif new not in text:
        raise SystemExit(f'ERROR: expected Flight Log date cell not found: {old}')

helper = '''function formatFlightLogDateTime(value) {
  if (!value) {
    return "-";
  }

  const text = String(value).trim();
  const match = text.match(/^(\\d{4}-\\d{2}-\\d{2})[ T](\\d{2}:\\d{2})/);
  if (match) {
    return `${match[1]} ${match[2]}`;
  }

  return text;
}

'''

if 'function formatFlightLogDateTime(value)' not in text:
    marker = 'function profitClass(value) {'
    idx = text.find(marker)
    if idx == -1:
        raise SystemExit('ERROR: function profitClass not found; cannot place date formatter helper.')
    text = text[:idx] + helper + text[idx:]

if text == original:
    print('No changes needed: Flight Log date formatting already patched.')
else:
    path.write_text(text, encoding='utf-8')
    print('Patched src/js/flight-log.js: departure and arrival now render as yyyy-MM-dd HH:mm.')
